  'use strict'

require('dotenv').config();
const { lightpanda } = require('@lightpanda/browser');
const puppeteer = require('puppeteer-core');
const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Error: link and prompt are required');
    console.error('Usage: node index.js <link> <prompt> [metadata_json]');
    console.error('Example: node index.js "https://news.ycombinator.com" "Search for lightpanda and extract results" \'{"port":9222}\'');
    process.exit(1);
  }

  const link = args[0];
  const prompt = args[1];
  let metadata = {};

  if (args[2]) {
    try {
      metadata = JSON.parse(args[2]);
    } catch (e) {
      console.error('Error: metadata must be valid JSON');
      process.exit(1);
    }
  }

  return { link, prompt, metadata };
}

async function getPageContext(page) {
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

    const links = Array.from(document.querySelectorAll('a')).slice(0, 20).map(a => ({
      text: a.textContent?.trim(),
      href: a.href
    }));

    return {
      title: document.title,
      url: window.location.href,
      inputs: inputs.filter(i => i.selector),
      buttons: buttons.filter(b => b.selector),
      links: links,
      bodyPreview: document.body.innerText.substring(0, 1000)
    };
  });
}

async function askAI(openai, pageContext, userPrompt, conversationHistory = []) {
  const systemPrompt = `You are a web scraping assistant. You analyze web pages and decide what actions to take.

Available actions:
1. TYPE: Type text into an input field
   Format: {"action": "type", "selector": "input selector", "text": "text to type", "reasoning": "why you're doing this"}

2. PRESS_ENTER: Press Enter key on an input field (use after typing to submit forms)
   Format: {"action": "press_enter", "selector": "input selector", "reasoning": "why you're doing this"}

3. CLICK: Click a button or link
   Format: {"action": "click", "selector": "button/link selector", "reasoning": "why you're doing this"}

4. WAIT: Wait for an element to appear
   Format: {"action": "wait", "selector": "element selector", "timeout": 5000, "reasoning": "why you're doing this"}
git fetch origin
git rebase origin/main

5. EXTRACT: Extract data from the page
   Format: {"action": "extract", "script": "JavaScript code that returns the data", "reasoning": "why you're doing this"}

6. DONE: Finish and return results
   Format: {"action": "done", "result": "final data or message", "reasoning": "why you're done"}

Important:
- After typing in a search box, use PRESS_ENTER to submit the search
- Don't repeat the same action if it didn't work - try a different approach
- If you've tried 3 times without progress, use EXTRACT or DONE with what you have
- ALWAYS include a "reasoning" field explaining what you observed and why you're taking this action

Respond with a JSON object containing the next action to take. Be concise and efficient.`;

  const messages = [
    { role: 'system', content: systemPrompt },
    ...conversationHistory,
    {
      role: 'user',
      content: `User's goal: ${userPrompt}\n\nCurrent page state:\n${JSON.stringify(pageContext, null, 2)}\n\nWhat should I do next?`
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

(async () => {
  const { link, prompt, metadata } = parseArgs();

  // Create session ID and folder
  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '_'); // HH_MM_SS
  const sessionId = Math.random().toString(36).substring(2, 8); // 6 char random ID
  const sessionName = `${timeStr}_${sessionId}`;
  const sessionDir = path.join(__dirname, 'sessions', sessionName);

  // Create sessions directory
  fs.mkdirSync(sessionDir, { recursive: true });

  console.error(`\n═══════════════════════════════════════════════════════`);
  console.error(`Session ID: ${sessionName}`);
  console.error(`Session Dir: ${sessionDir}`);
  console.error(`═══════════════════════════════════════════════════════\n`);

  // Session log object
  const sessionLog = {
    sessionId: sessionName,
    timestamp: now.toISOString(),
    url: link,
    prompt: prompt,
    metadata: metadata,
    steps: [],
    result: null,
    error: null
  };

  // Get OpenAI API key from environment or metadata
  const apiKey = metadata.openaiApiKey || process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error('Error: OpenAI API key required. Set OPENAI_API_KEY env var or pass in metadata');
    process.exit(1);
  }

  const openai = new OpenAI({ apiKey });

  // Extract metadata with defaults
  const port = metadata.port || 9222;
  const maxSteps = metadata.maxSteps || 10;

  const lpdopts = {
    host: '127.0.0.1',
    port: port,
  };

  const puppeteeropts = {
    browserWSEndpoint: 'ws://' + lpdopts.host + ':' + lpdopts.port,
  };


  let proc, browser, context, page;

  try {
    // Start Lightpanda browser in a separate process.
    proc = await lightpanda.serve(lpdopts);

    // Connect Puppeteer to the browser.
    browser = await puppeteer.connect(puppeteeropts);
    context = await browser.createBrowserContext();
    page = await context.newPage();

    // Go to target URL
    await page.goto(link);

    const conversationHistory = [];
    let stepCount = 0;
    let finalResult = null;

    // AI-driven loop
    while (stepCount < maxSteps) {
      stepCount++;

      const stepLog = {
        step: stepCount,
        timestamp: new Date().toISOString(),
        pageContext: null,
        aiObservation: null,
        action: null,
        result: null,
        error: null
      };

      try {
        // Get current page context
        const pageContext = await getPageContext(page);
        stepLog.pageContext = pageContext;

        console.error(`\n─────────────────────────────────────────────────────`);
        console.error(`📍 Step ${stepCount} | Page: ${pageContext.title}`);
        console.error(`🔗 URL: ${pageContext.url}`);

        // Ask AI what to do next
        const action = await askAI(openai, pageContext, prompt, conversationHistory);
        stepLog.action = action;
        stepLog.aiObservation = action.reasoning || 'No reasoning provided';

        // Log AI's observation and decision
        console.error(`\n🤖 AI Observation: ${stepLog.aiObservation}`);
        console.error(`⚡ Action: ${action.action.toUpperCase()}`);
        if (action.selector) console.error(`🎯 Target: ${action.selector}`);
        if (action.text) console.error(`📝 Text: "${action.text}"`);

        // Add to conversation history
        conversationHistory.push(
          { role: 'user', content: `Current page: ${pageContext.url}` },
          { role: 'assistant', content: JSON.stringify(action) }
        );

        // Execute the action (normalize to lowercase)
        const actionType = action.action.toLowerCase();
        let executionResult = null;

        switch (actionType) {
          case 'type':
            await page.type(action.selector, action.text);
            executionResult = `Typed "${action.text}" into ${action.selector}`;
            break;

          case 'press_enter':
            await page.focus(action.selector);
            await page.keyboard.press('Enter');
            // Wait for page to load
            await new Promise(resolve => setTimeout(resolve, 2000));
            executionResult = `Pressed Enter on ${action.selector}`;
            break;

          case 'click':
            await page.click(action.selector);
            // Wait a bit for page to respond
            await new Promise(resolve => setTimeout(resolve, 1000));
            executionResult = `Clicked ${action.selector}`;
            break;

          case 'wait':
            await page.waitForSelector(action.selector, { timeout: action.timeout || 5000 });
            executionResult = `Waited for ${action.selector}`;
            break;

          case 'extract':
            const data = await page.evaluate(action.script);
            conversationHistory.push({ role: 'user', content: `Extracted data: ${JSON.stringify(data)}` });
            executionResult = `Extracted: ${JSON.stringify(data).substring(0, 100)}...`;
            stepLog.extractedData = data;
            break;

          case 'done':
            finalResult = action.result;
            executionResult = 'Task completed';
            break;

          default:
            executionResult = `Unknown action: ${action.action}`;
            console.error(`❌ ${executionResult}`);
        }

        stepLog.result = executionResult;
        console.error(`✅ Result: ${executionResult}`);

        // Save screenshot
        try {
          const screenshotPath = path.join(sessionDir, `step_${stepCount}.png`);
          await page.screenshot({ path: screenshotPath });
          stepLog.screenshot = `step_${stepCount}.png`;
        } catch (e) {
          // Screenshot failed, continue anyway
        }

        // If done, break the loop
        if (actionType === 'done') {
          sessionLog.result = finalResult;
          console.log(JSON.stringify(finalResult, null, 2));
          break;
        }

      } catch (error) {
        stepLog.error = error.message;
        console.error(`❌ Error in step ${stepCount}: ${error.message}`);
      }

      // Save step log
      sessionLog.steps.push(stepLog);
    }

    if (stepCount >= maxSteps) {
      console.error('\n⚠️  Warning: Reached maximum steps without completion');
      sessionLog.error = 'Reached maximum steps without completion';
    }

  } catch (error) {
    sessionLog.error = error.message;
    console.error('Error:', error.message);
  } finally {
    // Save session log
    try {
      const logPath = path.join(sessionDir, 'session.json');
      fs.writeFileSync(logPath, JSON.stringify(sessionLog, null, 2));
      console.error(`\n═══════════════════════════════════════════════════════`);
      console.error(`✅ Session log saved to: ${logPath}`);
      console.error(`═══════════════════════════════════════════════════════\n`);
    } catch (e) {
      console.error(`Failed to save session log: ${e.message}`);
    }

    // Cleanup
    if (page) await page.close();
    if (context) await context.close();
    if (browser) await browser.disconnect();
    if (proc) {
      proc.stdout.destroy();
      proc.stderr.destroy();
      proc.kill();
    }

    // Exit with appropriate code
    if (sessionLog.error) {
      process.exit(1);
    }
  }
})();
