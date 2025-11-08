# portfolioGuardian
Notifies users if they need to take action on their portfolio.

## Setup (zsh)
1. **OpenAI Key**  
   ```bash
   echo 'export OPENAI_API_KEY="sk-yourkeyhere"' >> ~/.zshrc
   source ~/.zshrc
   ```
2. **Email SMTP Password**  
   Ask Teo for his password.  
   ```bash
   echo 'export SMTP_PASSWORD="paste password"' >> ~/.zshrc
   source ~/.zshrc
   ```
3. **Weaviate Settings**  
   ```bash
   echo 'export WEAVIATE_URL="your-weaviate-url"' >> ~/.zshrc
   echo 'export WEAVIATE_API_KEY="your-weaviate-api-key"' >> ~/.zshrc
   source ~/.zshrc
   ```

---

## Setup (bash)
1. **OpenAI Key**  
   ```bash
   echo 'export OPENAI_API_KEY="sk-yourkeyhere"' >> ~/.bash_profile
   source ~/.bash_profile
   ```
2. **Email SMTP Password**  
   Ask Teo for his password.  
   ```bash
   echo 'export SMTP_PASSWORD="paste password"' >> ~/.bash_profile
   source ~/.bash_profile
   ```
3. **Weaviate Settings**  
   ```bash
   echo 'export WEAVIATE_URL="your-weaviate-url"' >> ~/.bash_profile
   echo 'export WEAVIATE_API_KEY="your-weaviate-api-key"' >> ~/.bash_profile
   source ~/.bash_profile
   ```
