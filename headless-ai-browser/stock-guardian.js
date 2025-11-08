'use strict'

require('dotenv').config();
const puppeteer = require('puppeteer-core');
const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.error('Error: topic, goal, and sources are required');
    console.error('Usage: node stock-guardian.js <topic> <goal> <sources_json> [metadata_json]');
    console.error('Example: node stock-guardian.js "AAPL" "Monitor Apple stock for investment risks and opportunities" \'["https://news.ycombinator.com","https://finance.yahoo.com"]\' \'{"maxStepsPerSource":15}\'');
    process.exit(1);
  }

  const topic = args[0];
  const goal = args[1];
  let sources = [];

  try {
    sources = JSON.parse(args[2]);
  } catch (e) {
    console.error('Error: sources must be valid JSON array');
    process.exit(1);
  }

  let metadata = {};
  if (args[3]) {
    try {
      metadata = JSON.parse(args[3]);
    } catch (e) {
      console.error('Error: metadata must be valid JSON');
      process.exit(1);
    }
  }

  return { topic, goal, sources, metadata };
}

async function getPageContext(page) {
  try {
    // Wait for page to be ready
    await page.waitForSelector('body', { timeout: 5000 });

    return await page.evaluate(() => {
      // Get page structure
      const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
        type: input.type,
        name: input.name,
        id: input.id,
        placeholder: input.placeholder,
        selector: input.id ? `#${input.id}` : input.name ? `input[name="${input.name}"]` : null
      }));

      const buttons = Array.from(document.querySelectorAll('button, input[type="submit"]')).map(btn => ({
        text: btn.textContent?.trim() || btn.value,
        id: btn.id,
        selector: btn.id ? `#${btn.id}` : null
      }));

      // Get more links for better crawling (100 instead of 40)
      const links = Array.from(document.querySelectorAll('a')).slice(0, 100).map(a => ({
        text: a.textContent?.trim(),
        href: a.href
      }));

      const articles = Array.from(document.querySelectorAll('article, .article, .post, .story')).slice(0, 10).map(article => ({
        text: article.textContent?.trim()
      }));

      return {
        title: document.title,
        url: window.location.href,
        inputs: inputs.filter(i => i.selector),
        buttons: buttons.filter(b => b.selector),
        links: links,
        articles: articles,
        bodyPreview: document.body.innerText.substring(0, 3000)
      };
    });
  } catch (error) {
    // If frame is detached, return minimal context
    console.error('Warning: Could not get full page context:', error.message);
    return {
      title: 'Unknown',
      url: page.url(),
      inputs: [],
      buttons: [],
      links: [],
      articles: [],
      bodyPreview: 'Page context unavailable'
    };
  }
}

async function extractFullArticle(page) {
  try {
    // Wait for content to load
    await page.waitForSelector('body', { timeout: 5000 });

    return await page.evaluate(() => {
      // Try to find the main article content
      const selectors = [
        'article',
        '.article-content',
        '.post-content',
        '.entry-content',
        'main article',
        '[role="article"]',
        '.story-body',
        '#article-body'
      ];

      let content = '';
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
          content = element.innerText;
          break;
        }
      }

      // Fallback to main content if no article found
      if (!content) {
        const main = document.querySelector('main') || document.querySelector('#main') || document.body;
        content = main.innerText;
      }

      return {
        url: window.location.href,
        title: document.title,
        content: content,
        timestamp: new Date().toISOString(),
        headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText.trim()),
        links: Array.from(document.querySelectorAll('a')).map(a => ({
          text: a.innerText.trim(),
          href: a.href
        })).filter(l => l.text && l.href)
      };
    });
  } catch (error) {
    console.error('Warning: Could not extract article:', error.message);
    return {
      url: page.url(),
      title: 'Extraction failed',
      content: 'Could not extract article content',
      timestamp: new Date().toISOString(),
      headings: [],
      links: []
    };
  }
}

async function askStockGuardianAI(openai, pageContext, topic, goal, currentThoughts, conversationHistory = [], urlUnchangedCount = 0) {
  const systemPrompt = `You are a Web Crawler AI Agent with the following mission:

📌 TOPIC: ${topic}
🎯 GOAL: ${goal}

PRIMARY STRATEGY - WEB CRAWLER MODE:
You should PRIMARILY operate as a web crawler, meaning:
1. **NAVIGATE first, interact second**: Your main action should be NAVIGATE to follow links
2. **Follow ${topic}-related links aggressively**: Look through the "links" array and NAVIGATE to any URL relevant to "${topic}" and your goal
3. **Extract when you land on relevant pages**: Use EXTRACT_ARTICLE when you've navigated to a page with substantial content related to your goal
4. **Record insights as you go**: Use RECORD_THOUGHT to capture key observations that help achieve your goal
5. **Keep moving**: Don't get stuck on one page - if you've extracted content, move to the next link

⚠️ ONLY use TYPE/CLICK/SCROLL if:
- You're on the initial landing page and see a search box (then search for "${topic}")
- There are NO relevant links visible in the links array
- You need to scroll to reveal more links

📋 Available actions:
1. NAVIGATE: Go directly to a URL from the links array (PREFERRED ACTION)
   Format: {"action": "navigate", "url": "https://...", "reasoning": "why this link helps achieve the goal"}

2. EXTRACT_ARTICLE: Extract full article content from current page
   Format: {"action": "extract_article", "reasoning": "why this article is relevant to the goal"}

3. RECORD_THOUGHT: Record important insights
   Format: {"action": "record_thought", "thought": "your analysis/observation", "sentiment": "positive|negative|neutral", "importance": "high|medium|low", "reasoning": "why this matters for the goal"}

4. SCROLL: Scroll to see more links
   Format: {"action": "scroll", "direction": "down", "pixels": 500, "reasoning": "to reveal more relevant links"}

5. TYPE: Type text into search field (ONLY on landing pages)
   Format: {"action": "type", "selector": "input selector", "text": "${topic}", "reasoning": "searching for ${topic}"}

6. PRESS_ENTER: Submit search forms
   Format: {"action": "press_enter", "selector": "input selector", "reasoning": "submit search for ${topic}"}

7. CLICK: Click buttons (rarely needed)
   Format: {"action": "click", "selector": "button selector", "reasoning": "why"}

8. DONE: Complete monitoring session
   Format: {"action": "done", "summary": "overall summary of findings related to the goal", "reasoning": "why you're done"}

🔥 DECISION TREE (follow this order):
1. Check if current page has substantial content related to your goal → EXTRACT_ARTICLE
2. Look at "links" array for ${topic}-related URLs → NAVIGATE to most relevant
3. If no relevant links visible → SCROLL down to load more
4. If on landing page with search box and no relevant links → TYPE "${topic}" then PRESS_ENTER
5. If you've gathered 3+ articles and insights relevant to your goal → consider DONE

Remember: You're a CRAWLER focused on achieving your goal. Follow links, extract content, and move on. Don't overthink interactions.

Respond with ONLY a valid JSON object.`;

  const messages = [
    { role: 'system', content: systemPrompt },
    ...conversationHistory,
    {
      role: 'user',
      content: `Current Thoughts:\n${currentThoughts}\n\nCurrent page state:\n${JSON.stringify(pageContext, null, 2)}\n\nWhat should I do next to achieve the goal?`
    }
  ];

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: messages,
    temperature: 0.7,
  });

  const content = response.choices[0].message.content;

  // Try to extract JSON from the response
  const jsonMatch = content.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    return { fullResponse: content, ...JSON.parse(jsonMatch[0]) };
  }

  throw new Error('AI did not return valid JSON action');
}

function appendToThoughts(thoughtsFile, thought) {
  const timestamp = new Date().toISOString();
  const entry = `\n[${timestamp}] ${thought.sentiment ? `[${thought.sentiment.toUpperCase()}]` : ''} ${thought.importance ? `[${thought.importance.toUpperCase()}]` : ''}\n${thought.thought}\n`;
  fs.appendFileSync(thoughtsFile, entry);
}

function saveArticle(articlesDir, url, articleData) {
  const urlHash = Buffer.from(url).toString('base64').replace(/[^a-zA-Z0-9]/g, '').substring(0, 32);
  const filename = `article_${urlHash}.json`;
  const filepath = path.join(articlesDir, filename);

  fs.writeFileSync(filepath, JSON.stringify(articleData, null, 2));
  return filename;
}

async function generatePageSummary(openai, pageContext, topic, goal) {
  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: `You are an expert analyst. Summarize the key information relevant to "${topic}" from the provided webpage content. Focus on information that helps achieve this goal: "${goal}". Be concise (3-5 sentences).`
        },
        {
          role: 'user',
          content: `Page title: ${pageContext.title}\nURL: ${pageContext.url}\n\nContent:\n${pageContext.bodyPreview}`
        }
      ],
      temperature: 0.5,
      max_tokens: 200
    });

    return response.choices[0].message.content;
  } catch (error) {
    console.error(`⚠️  Warning: Failed to generate summary: ${error.message}`);
    return 'Summary generation failed';
  }
}

async function generateStepSummaryForDB(openai, pageContext, topic, goal, action, allLinks) {
  try {
    // Extract explored links from the action and page
    const exploredLinks = allLinks.slice(0, 10).map(l => `- ${l.text}: ${l.href}`).join('\n');

    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: `You are creating a database entry for a research step about "${topic}".

Goal: ${goal}

Generate a JSON object with these fields:
- "signal": "Positive", "Negative", or "Neutral" - based on whether the information found is favorable, unfavorable, or neutral for ${topic}
- "title": A concise headline (max 10 words) describing what was found
- "body": A detailed summary (2-4 sentences) of the key findings. IMPORTANT: Include mentions of important links explored from the list provided.

Respond ONLY with valid JSON in this format:
{"signal": "...", "title": "...", "body": "..."}`
        },
        {
          role: 'user',
          content: `Page: ${pageContext.title}
URL: ${pageContext.url}

Action taken: ${action.action} - ${action.reasoning}

Content preview:
${pageContext.bodyPreview.substring(0, 1000)}

Links explored on this page:
${exploredLinks}

Generate the database entry:`
        }
      ],
      temperature: 0.7,
      max_tokens: 300
    });

    const content = response.choices[0].message.content;
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    // Fallback if JSON parsing fails
    return {
      signal: "Neutral",
      title: `Research step on ${topic}`,
      body: `Explored ${pageContext.url} - ${action.reasoning}`
    };
  } catch (error) {
    console.error(`⚠️  Warning: Failed to generate step summary: ${error.message}`);
    return {
      signal: "Neutral",
      title: `Research step on ${topic}`,
      body: `Explored ${pageContext.url}`
    };
  }
}

async function insertToDatabase(topic, signal, title, body, weaviateUrl, weaviateApiKey) {
  try {
    // Use Python script to insert into Weaviate
    const { execSync } = require('child_process');

    const pythonScript = `
import weaviate
from weaviate.classes.init import Auth
from datetime import datetime
import sys

try:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url="${weaviateUrl}",
        auth_credentials=Auth.api_key("${weaviateApiKey}"),
    )

    news = client.collections.get("News")

    news.data.insert({
        "ticker": ${JSON.stringify(topic)},
        "signal": ${JSON.stringify(signal)},
        "title": ${JSON.stringify(title)},
        "body": ${JSON.stringify(body)},
        "time": datetime.now().strftime("%Y-%m-%d")
    })

    client.close()
    print("✅ Inserted to database")
except Exception as e:
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    sys.exit(1)
`;

    // Use uv run python to ensure weaviate-client is available
    const result = execSync('uv run python -c ' + JSON.stringify(pythonScript), {
      encoding: 'utf8',
      timeout: 10000,
      cwd: __dirname
    });

    console.error(`✅ Database insert successful: ${result.trim()}`);
    return true;
  } catch (error) {
    console.error(`⚠️  Warning: Database insert failed: ${error.message}`);
    if (error.stderr) {
      console.error(`   Stderr: ${error.stderr}`);
    }
    if (error.stdout) {
      console.error(`   Stdout: ${error.stdout}`);
    }
    return false;
  }
}

(async () => {
  const { topic, goal, sources, metadata } = parseArgs();

  // Create session ID and folder
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
  const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '_'); // HH_MM_SS
  const sessionId = Math.random().toString(36).substring(2, 8);
  const sessionName = `${topic.replace(/[^a-zA-Z0-9]/g, '_')}_${dateStr}_${timeStr}_${sessionId}`;
  const sessionDir = path.join(__dirname, 'sessions', sessionName);

  // Create session directory structure
  fs.mkdirSync(sessionDir, { recursive: true });
  const articlesDir = path.join(sessionDir, 'articles');
  fs.mkdirSync(articlesDir, { recursive: true });

  console.error(`\n═══════════════════════════════════════════════════════`);
  console.error(`🔍 Web Crawler AI - Research Agent`);
  console.error(`Session: ${sessionName}`);
  console.error(`Topic: ${topic}`);
  console.error(`Goal: ${goal}`);
  console.error(`Sources: ${sources.join(', ')}`);
  console.error(`═══════════════════════════════════════════════════════\n`);

  // Initialize thought file
  const thoughtsFile = path.join(sessionDir, 'current_thoughts.txt');
  const thoughtsHeader = `Web Crawler AI - Research Session\nTopic: ${topic}\nGoal: ${goal}\nSession: ${sessionName}\nStarted: ${now.toISOString()}\n${'='.repeat(60)}\n`;
  fs.writeFileSync(thoughtsFile, thoughtsHeader);

  // Session log object
  const sessionLog = {
    sessionId: sessionName,
    topic: topic,
    goal: goal,
    timestamp: now.toISOString(),
    sources: sources,
    metadata: metadata,
    steps: [],
    articlesCollected: [],
    thoughts: [],
    result: null,
    error: null
  };

  // Get OpenAI API key
  const apiKey = metadata.openaiApiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error('Error: OpenAI API key required. Set OPENAI_API_KEY env var or pass in metadata');
    process.exit(1);
  }

  const openai = new OpenAI({ apiKey });

  // Get LightPanda cloud token
  const lpdToken = process.env.LPD_TOKEN;
  if (!lpdToken) {
    console.error('Error: LPD_TOKEN env var required for LightPanda cloud');
    process.exit(1);
  }

  // Extract metadata with defaults
  const maxStepsPerSource = metadata.maxStepsPerSource || 20;

  const puppeteeropts = {
    browserWSEndpoint: 'wss://euwest.cloud.lightpanda.io/ws?browser=chrome&token=' + lpdToken,
  };

  let browser, context, page;

  try {
    // Connect to LightPanda cloud browser
    console.error('🚀 Connecting to LightPanda cloud...');
    browser = await puppeteer.connect(puppeteeropts);
    context = await browser.createBrowserContext();
    page = await context.newPage();

    // Process each source
    for (let sourceIdx = 0; sourceIdx < sources.length; sourceIdx++) {
      const source = sources[sourceIdx];

      console.error(`\n${'='.repeat(60)}`);
      console.error(`📰 Source ${sourceIdx + 1}/${sources.length}: ${source}`);
      console.error(`${'='.repeat(60)}\n`);

      try {
        await page.goto(source, {
          waitUntil: 'domcontentloaded',
          timeout: 30000
        });
        // Give page time to fully render
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        console.error(`❌ Failed to load source ${source}: ${error.message}`);
        continue; // Skip to next source
      }

      const conversationHistory = [];
      let stepCount = 0;
      let sourceComplete = false;
      let previousUrl = null;
      let urlUnchangedCount = 0;

      while (stepCount < maxStepsPerSource && !sourceComplete) {
        stepCount++;

        const stepLog = {
          source: source,
          step: stepCount,
          timestamp: new Date().toISOString(),
          pageContext: null,
          action: null,
          result: null,
          error: null
        };

        try {
          // Get current page context
          const pageContext = await getPageContext(page);
          stepLog.pageContext = { title: pageContext.title, url: pageContext.url };

          console.error(`\n─────────────────────────────────────────────────────`);
          console.error(`📍 Step ${stepCount} | ${pageContext.title}`);
          console.error(`🔗 ${pageContext.url}`);

          // Track URL changes for crawler fallback
          if (previousUrl !== null && previousUrl === pageContext.url) {
            urlUnchangedCount++;
            console.error(`⚠️  URL unchanged for ${urlUnchangedCount} step(s) - may trigger crawler mode`);
          }

          // Read current thoughts
          const currentThoughts = fs.readFileSync(thoughtsFile, 'utf8');

          // Ask AI what to do (pass urlUnchangedCount to encourage navigation if stuck)
          const action = await askStockGuardianAI(openai, pageContext, topic, goal, currentThoughts, conversationHistory, urlUnchangedCount);
          stepLog.action = action;

          console.error(`\n🤖 AI: ${action.reasoning}`);
          console.error(`⚡ Action: ${action.action.toUpperCase()}`);

          // Add to conversation history
          conversationHistory.push(
            { role: 'user', content: `Page: ${pageContext.url}` },
            { role: 'assistant', content: JSON.stringify({ action: action.action, reasoning: action.reasoning }) }
          );

          // Keep history manageable
          if (conversationHistory.length > 8) {
            conversationHistory.splice(0, conversationHistory.length - 8);
          }

          // Execute action
          const actionType = action.action.toLowerCase();
          let executionResult = null;

          switch (actionType) {
            case 'type':
              try {
                await page.waitForSelector(action.selector, { timeout: 3000 });
                await page.type(action.selector, action.text);
                executionResult = `Typed "${action.text}"`;
                console.error(`✅ ${executionResult}`);
              } catch (e) {
                throw new Error(`Could not type in ${action.selector}: ${e.message}`);
              }
              break;

            case 'press_enter':
              try {
                await page.waitForSelector(action.selector, { timeout: 3000 });
                await page.focus(action.selector);
                await page.keyboard.press('Enter');
                // Wait for navigation or page load
                await Promise.race([
                  page.waitForNavigation({ timeout: 5000, waitUntil: 'domcontentloaded' }).catch(() => {}),
                  new Promise(resolve => setTimeout(resolve, 3000))
                ]);
                executionResult = 'Pressed Enter, waiting for results';
                console.error(`✅ ${executionResult}`);
              } catch (e) {
                throw new Error(`Could not press enter on ${action.selector}: ${e.message}`);
              }
              break;

            case 'click':
              try {
                await page.waitForSelector(action.selector, { timeout: 3000 });
                // Use Promise.race to handle navigation or timeout
                await Promise.all([
                  page.click(action.selector),
                  Promise.race([
                    page.waitForNavigation({ timeout: 5000, waitUntil: 'domcontentloaded' }).catch(() => {}),
                    new Promise(resolve => setTimeout(resolve, 2000))
                  ])
                ]);
                executionResult = `Clicked ${action.selector}`;
                console.error(`✅ ${executionResult}`);
              } catch (e) {
                throw new Error(`Could not click ${action.selector}: ${e.message}`);
              }
              break;

            case 'wait':
              await page.waitForSelector(action.selector, { timeout: action.timeout || 5000 });
              executionResult = `Waited for ${action.selector}`;
              console.error(`✅ ${executionResult}`);
              break;

            case 'scroll':
              const direction = action.direction || 'down';
              const pixels = action.pixels || 500;
              await page.evaluate((dir, px) => {
                if (dir === 'down') window.scrollBy(0, px);
                else if (dir === 'up') window.scrollBy(0, -px);
              }, direction, pixels);
              await new Promise(resolve => setTimeout(resolve, 500));
              executionResult = `Scrolled ${direction}`;
              console.error(`✅ ${executionResult}`);
              break;

            case 'navigate':
              try {
                await page.goto(action.url, {
                  waitUntil: 'domcontentloaded',
                  timeout: 30000
                });
                await new Promise(resolve => setTimeout(resolve, 2000));
                executionResult = `Navigated to ${action.url}`;
                console.error(`✅ ${executionResult}`);
              } catch (e) {
                throw new Error(`Could not navigate to ${action.url}: ${e.message}`);
              }
              break;

            case 'extract_article':
              const articleData = await extractFullArticle(page);
              const filename = saveArticle(articlesDir, articleData.url, articleData);
              sessionLog.articlesCollected.push({
                url: articleData.url,
                title: articleData.title,
                filename: filename,
                timestamp: articleData.timestamp
              });
              executionResult = `Extracted article: ${articleData.title}`;
              console.error(`✅ ${executionResult}`);
              console.error(`📄 Saved to: ${filename}`);
              break;

            case 'record_thought':
              appendToThoughts(thoughtsFile, action);
              sessionLog.thoughts.push({
                thought: action.thought,
                sentiment: action.sentiment,
                importance: action.importance,
                timestamp: new Date().toISOString()
              });
              executionResult = `Recorded thought: ${action.thought.substring(0, 100)}...`;
              console.error(`✅ ${executionResult}`);
              break;

            case 'done':
              sourceComplete = true;
              executionResult = `Completed source: ${action.summary}`;
              console.error(`✅ ${executionResult}`);
              break;

            default:
              executionResult = `Unknown action: ${action.action}`;
              console.error(`❌ ${executionResult}`);
          }

          stepLog.result = executionResult;

          // Save screenshot
          try {
            const screenshotPath = path.join(sessionDir, `source${sourceIdx + 1}_step${stepCount}.png`);
            await page.screenshot({ path: screenshotPath });
            stepLog.screenshot = `source${sourceIdx + 1}_step${stepCount}.png`;
          } catch (e) {
            // Screenshot failed, continue
          }

          // Save page context to articles directory only if URL changed
          const currentUrl = pageContext.url;
          const urlChanged = previousUrl !== currentUrl;

          if (urlChanged) {
            console.error(`🔄 URL changed from ${previousUrl || 'initial'} to ${currentUrl}`);

            // Reset unchanged counter since we successfully navigated
            urlUnchangedCount = 0;

            try {
              // Generate AI summary of the page
              console.error(`🤖 Generating AI summary...`);
              const aiSummary = await generatePageSummary(openai, pageContext, topic, goal);

              // Extract all links
              const allLinks = pageContext.links.filter(link => link.href && link.text);

              const contextFilename = `source${sourceIdx + 1}_step${stepCount}.json`;
              const contextPath = path.join(articlesDir, contextFilename);
              fs.writeFileSync(contextPath, JSON.stringify({
                step: stepCount,
                source: source,
                timestamp: stepLog.timestamp,
                url: currentUrl,
                title: pageContext.title,
                aiSummary: aiSummary,
                allLinks: allLinks,
                pageContext: pageContext,
                action: action,
                result: executionResult
              }, null, 2));
              console.error(`💾 Saved context to: ${contextFilename}`);
              console.error(`📝 Summary: ${aiSummary.substring(0, 100)}...`);
              console.error(`🔗 Found ${allLinks.length} links`);

              // Generate database entry and insert
              const weaviateUrl = metadata.weaviateUrl || process.env.WEAVIATE_URL || "v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud";
              const weaviateApiKey = metadata.weaviateApiKey || process.env.WEAVIATE_API_KEY || "WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw";

              if (weaviateUrl && weaviateApiKey) {
                console.error(`🗄️  Generating database entry...`);
                const dbEntry = await generateStepSummaryForDB(openai, pageContext, topic, goal, action, allLinks);
                console.error(`📊 DB Entry - Signal: ${dbEntry.signal}, Title: ${dbEntry.title}`);

                // Save database entry to JSON file
                const dbEntryFilename = `db_entry_source${sourceIdx + 1}_step${stepCount}.json`;
                const dbEntryPath = path.join(articlesDir, dbEntryFilename);
                const dbEntryData = {
                  ticker: topic,
                  signal: dbEntry.signal,
                  title: dbEntry.title,
                  body: dbEntry.body,
                  time: new Date().toISOString().split('T')[0], // YYYY-MM-DD
                  metadata: {
                    step: stepCount,
                    source: source,
                    url: currentUrl,
                    timestamp: stepLog.timestamp
                  }
                };
                fs.writeFileSync(dbEntryPath, JSON.stringify(dbEntryData, null, 2));
                console.error(`💾 Saved DB entry to: ${dbEntryFilename}`);

                await insertToDatabase(topic, dbEntry.signal, dbEntry.title, dbEntry.body, weaviateUrl, weaviateApiKey);
              }
            } catch (e) {
              console.error(`⚠️  Warning: Failed to save context to articles/${contextFilename}: ${e.message}`);
            }

            // Update previous URL
            previousUrl = currentUrl;
          } else {
            console.error(`⏭️  Skipping save - URL unchanged: ${currentUrl}`);
          }

        } catch (error) {
          stepLog.error = error.message;
          console.error(`❌ Error: ${error.message}`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        sessionLog.steps.push(stepLog);
      }

      if (!sourceComplete) {
        console.error(`\n⚠️  Reached max steps for source: ${source}`);
      }
    }

    // Final summary
    console.error(`\n${'='.repeat(60)}`);
    console.error(`📊 Research Complete`);
    console.error(`Topic: ${topic}`);
    console.error(`Articles collected: ${sessionLog.articlesCollected.length}`);
    console.error(`Thoughts recorded: ${sessionLog.thoughts.length}`);
    console.error(`${'='.repeat(60)}\n`);

    sessionLog.result = {
      topic: topic,
      goal: goal,
      articlesCollected: sessionLog.articlesCollected.length,
      thoughtsRecorded: sessionLog.thoughts.length,
      sourcesProcessed: sources.length
    };

    console.log(JSON.stringify(sessionLog.result, null, 2));

  } catch (error) {
    sessionLog.error = error.message;
    console.error('❌ Error:', error.message);
  } finally {
    // Save session log
    try {
      const logPath = path.join(sessionDir, 'session.json');
      fs.writeFileSync(logPath, JSON.stringify(sessionLog, null, 2));
      console.error(`\n✅ Session saved to: ${sessionDir}`);
      console.error(`   - Thoughts: current_thoughts.txt`);
      console.error(`   - Articles: articles/`);
      console.error(`   - Log: session.json\n`);
    } catch (e) {
      console.error(`Failed to save session: ${e.message}`);
    }

    // Cleanup
    if (page) await page.close();
    if (context) await context.close();
    if (browser) await browser.disconnect();

    if (sessionLog.error) {
      process.exit(1);
    }
  }
})();
