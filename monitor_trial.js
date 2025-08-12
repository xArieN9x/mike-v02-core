require('dotenv').config();
const axios = require('axios');
const { exec } = require('child_process');

// Config
const CHECK_INTERVAL = 6 * 60 * 60 * 1000; // check every 6 jam
const TRIAL_THRESHOLD_DAYS = 3; // trigger auto-reset kalau ≤ 3 hari
let trialEndDate = new Date('2025-09-06'); // Update ikut tarikh luput Railway

// === Fungsi hantar Telegram ===
async function sendTelegramMessage(message) {
    const botToken = process.env.BOT_TOKEN;
    const chatId = process.env.CHAT_ID;
    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;

    try {
        await axios.post(url, {
            chat_id: chatId,
            text: message,
            parse_mode: 'Markdown'
        });
        console.log("✅ Mesej Telegram dihantar.");
    } catch (error) {
        console.error("❌ Gagal hantar mesej:", error.response ? error.response.data : error.message);
    }
}

// === Fungsi utama check trial ===
async function checkTrialStatus() {
    const now = new Date();
    const diffDays = Math.ceil((trialEndDate - now) / (1000 * 60 * 60 * 24));
    console.log(`Days left for Railway trial: ${diffDays}`);

    if (diffDays <= TRIAL_THRESHOLD_DAYS) {
        console.log('Trial ending soon! Triggering auto-reset...');

        // === Hantar notis Telegram ===
        let alertMsg = `🚨 *Railway Trial Hampir Tamat!*\n\nBaki: ${diffDays} hari.\n\nSila login & jawab captcha di sini:\nhttps://railway.app/`;
        await sendTelegramMessage(alertMsg);

        // === Auto deploy & register ===
        exec('node deploy_railway.js', (error, stdout, stderr) => {
            if (error) {
                console.error(`Deploy error: ${error.message}`);
                return;
            }
            console.log(`Deploy output:\n${stdout}`);

            exec('node register_railway.js', (regErr, regStdout, regStderr) => {
                if (regErr) {
                    console.error(`Register error: ${regErr.message}`);
                    return;
                }
                console.log(`Register output:\n${regStdout}`);
            });
        });
    }
}

// Auto check ikut interval
setInterval(checkTrialStatus, CHECK_INTERVAL);
checkTrialStatus();
