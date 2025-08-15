// telegramGPTBot.js
// Dependencies: node-telegram-bot-api, @supabase/supabase-js, openai, dotenv (optional for local)
require('dotenv').config();

const TelegramBot = require('node-telegram-bot-api');
const { createClient } = require('@supabase/supabase-js');
const OpenAI = require('openai');

// ENV required
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_ANON_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;

// OpenRouter API
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'meta-llama/llama-3.1-8b-instruct:free';

if (!TELEGRAM_BOT_TOKEN) {
  console.error('❌ TELEGRAM_BOT_TOKEN missing');
  process.exit(1);
}
if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.warn('⚠️ Supabase not configured (SUPABASE_URL/SUPABASE_ANON_KEY). DB writes will be skipped.');
}
if (!OPENROUTER_API_KEY) {
  console.error('❌ OPENROUTER_API_KEY missing');
  process.exit(1);
}

const supabase = (SUPABASE_URL && SUPABASE_KEY) ? createClient(SUPABASE_URL, SUPABASE_KEY) : null;
const openai = new OpenAI({
  apiKey: OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1'
});

function safeString(v) { return (v === undefined || v === null) ? '' : String(v); }

function startBot() {
  console.log('🔄 Starting Telegram bot (polling)...');
  const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: { restart: true } });

  bot.on('message', async (msg) => {
    const chatId = msg.chat && msg.chat.id;
    const userId = (msg.from && msg.from.id) ? String(msg.from.id) : 'unknown';
    const text = safeString(msg.text || msg.caption || '');

    console.log(`✉ Received from ${userId} (${chatId}): ${text}`);

    if (!text.trim()) return;

    try {
      if (supabase) {
        await supabase.from('chat_history').insert([{
          user_id: userId,
          source: 'telegram',
          message: text,
          response: null,
          ts: new Date().toISOString(),
          model: OPENAI_MODEL,
        }]);
      }
    } catch (e) {
      console.error('Supabase insert error (incoming):', e.message || e);
    }

    const messages = [
      { role: 'system', content: 'You are Mike, a helpful AI assistant for Pak Ya.' },
      { role: 'user', content: text }
    ];

    let aiReply = 'Maaf Pak Ya, ada masalah teknikal. Sila cuba lagi.';
    try {
      const completion = await openai.chat.completions.create({
        model: OPENAI_MODEL,
        messages,
        max_tokens: 700,
      });

      if (completion?.choices && completion.choices.length > 0) {
        aiReply = completion.choices[0].message?.content ?? aiReply;
      } else {
        console.warn('OpenRouter returned empty choices:', completion);
      }
    } catch (e) {
      console.error('OpenRouter error:', e.message || e);
    }

    try {
      await bot.sendMessage(chatId, aiReply, { parse_mode: 'HTML' });
    } catch (e) {
      console.error('Telegram sendMessage error:', e.message || e);
    }

    try {
      if (supabase) {
        const { data: rows } = await supabase
          .from('chat_history')
          .select('id')
          .eq('user_id', userId)
          .order('ts', { ascending: false })
          .limit(1);

        if (rows && rows.length > 0) {
          await supabase.from('chat_history').update({ response: aiReply }).match({ id: rows[0].id });
        }
      }
    } catch (e) {
      console.error('Supabase update error (response):', e.message || e);
    }
  });

  bot.on('polling_error', (error) => {
    console.error('❗ Polling error:', error?.code ?? '', error?.message ?? error);
  });

  bot.on('webhook_error', (error) => {
    console.error('❗ Webhook error (unexpected):', error);
  });

  setInterval(() => {
    console.log('⏱ heartbeat:', new Date().toISOString());
  }, 1000 * 60 * 5);
}

process.on('unhandledRejection', (reason) => {
  console.error('UnhandledRejection:', reason);
});
process.on('uncaughtException', (err) => {
  console.error('UncaughtException:', err);
  setTimeout(() => process.exit(1), 1000);
});

startBot();
