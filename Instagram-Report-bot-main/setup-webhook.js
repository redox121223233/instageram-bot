const https = require('https');

// This script can be run after deployment to set the webhook
// Usage: node setup-webhook.js YOUR_VERCEL_URL YOUR_BOT_TOKEN

const vercelUrl = process.env.VERCEL_URL || process.argv[2];
const botToken = process.env.BOT_TOKEN || process.argv[3];

if (!vercelUrl || !botToken) {
    console.error('Please provide Vercel URL and Bot Token');
    console.log('Usage: node setup-webhook.js <vercel-url> <bot-token>');
    process.exit(1);
}

const webhookUrl = `https://${vercelUrl}/api/webhook`;

const options = {
    hostname: 'api.telegram.org',
    path: `/bot${botToken}/setWebhook`,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
};

const postData = JSON.stringify({
    url: webhookUrl
});

const req = https.request(options, (res) => {
    let data = '';
    
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        const result = JSON.parse(data);
        if (result.ok) {
            console.log('✅ Webhook set successfully!');
            console.log(`Webhook URL: ${webhookUrl}`);
        } else {
            console.error('❌ Failed to set webhook:', result.description);
        }
    });
});

req.on('error', (error) => {
    console.error('Error setting webhook:', error);
});

req.write(postData);
req.end();