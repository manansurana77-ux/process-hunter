# Step by step

## A. Run the project on Ubuntu
1. Unzip and enter the folder: `unzip process_hunter_agent.zip && cd process_hunter_agent`
2. `sudo apt install python3-venv -y`
3. `python3 -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python3 -m pytest tests -v`   (expect 30 passed)
6. `export ANTHROPIC_API_KEY="your-key"` then `python3 main.py`

## B. Put it on GitHub
1. Create an account on github.com.
2. `sudo apt install git -y`
   `git config --global user.name "Your Name"`
   `git config --global user.email "your-github-email"`
3. On GitHub: + > New repository > name `process-hunter-agent` > Private >
   leave README unchecked > Create.
4. In the project folder:
   ```
   git init
   git add .
   git commit -m "Agentic AI Shell with Process Hunter Agent"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/process-hunter-agent.git
   git push -u origin main
   ```
5. When asked for a password, paste a Personal Access Token:
   GitHub > profile picture > Settings > Developer settings >
   Personal access tokens > Tokens (classic) > Generate (tick "repo").

## C. Add your teammate
Repository > Settings > Collaborators > Add people > type their GitHub username >
they accept the email invitation.

## D. Teammate downloads it
```
git clone https://github.com/YOUR-USERNAME/process-hunter-agent.git
cd process-hunter-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## E. Daily work
`git pull`  ->  change files  ->  `git add .`  ->  `git commit -m "what you did"`  ->  `git push`
