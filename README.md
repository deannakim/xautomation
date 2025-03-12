# Twitter Automation Bot

This project is an automated Twitter bot that posts tweets at regular intervals. It loads pre-written tweets from a list and publishes them automatically according to a set schedule.

## Key Features

- Automatic tweet posting at 8-hour intervals
- Tweet list loading from a JSON file
- Prevention of duplicate content errors
- Tweet index saving for continuity after restarts
- Detailed error logging

## Installation

1. Clone this repository:
```bash
git clone https://github.com/deannakim/xautomation.git
cd xautomation
```

2. Install the required packages:
```bash
pip install tweepy schedule python-dotenv
```

3. Set up your Twitter API keys:
   - Create a Twitter developer account and app at https://developer.twitter.com
   - Create a `tweepy_keys.env` file with the following format:
   ```
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   ```

4. Prepare your tweet list:
   - Write your tweets in a JSON array format in the `tweets.json` file
   - Example:
   ```json
   [
       "This is the content of the first tweet.",
       "This is the content of the second tweet.",
       "This is the content of the third tweet."
   ]
   ```

## Usage

To run the bot, use the following command:

```bash
python twitter_bot.py
```

- The bot will post the first tweet immediately upon starting
- It will then automatically post the next tweet every 8 hours
- To exit the program, press `Ctrl+C`

## Deployment

This bot can be deployed in various environments:

### Railway

1. Create a Railway account
2. Create a new project and connect your GitHub repository
3. Set up your Twitter API keys in the environment variables
4. Deploy

### Heroku

1. Create a Heroku account
2. Create a new app
3. Connect your GitHub repository
4. Set up your Twitter API keys in the environment variables
5. Deploy

## Troubleshooting

### 403 Forbidden Error

This error can occur for the following reasons:
- API keys are incorrect or expired
- Your app doesn't have permission to post tweets
- Your account is restricted or suspended

Solutions:
1. Verify your API keys in the Twitter developer portal
2. Ensure your app has "Read and Write" permissions
3. Check your Twitter account status

### Duplicate Content Error

This error occurs when trying to post tweets with identical content in a short time period.

Solutions:
- The bot automatically adds invisible characters to prevent this issue
- If the error persists, make your tweet content more diverse

## License

This project is distributed under the MIT License. See the LICENSE file for more information.

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## Contact

Project Maintainer: Deanna - saabsinthe@gmail.com

Project Link: [https://github.com/deannakim/xautomation](https://github.com/deannakim/xautomation)

---

Thank you for using this bot! If you have any issues or suggestions, please create an issue.
