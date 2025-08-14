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
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-3.5-turbo';

if (!TELEGRAM_BOT_TOKEN) {
  console.error('❌ TELEGRAM_BOT_TOKEN missing');
  process.exit(1);
}
if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.warn('⚠️ Supabase not configured (SUPABASE_URL/SUPABASE_ANON_KEY). DB writes will be skipped.');
}
if (!OPENAI_API_KEY) {
  console.error('❌ OPENAI_API_KEY missing');
  process.exit(1);
}

const supabase = (SUPABASE_URL && SUPABASE_KEY) ? createClient(SUPABASE_URL, SUPABASE_KEY) : null;
const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

function safeString(v) { return (v === undefined || v === null) ? '' : String(v); }

function startBot() {
  console.log('🔄 Starting Telegram bot (polling)...');
  const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: { restart: true } });

  // Generic message handler
  bot.on('message', async (msg) => {
    const chatId = msg.chat && msg.chat.id;
    const userId = (msg.from && msg.from.id) ? String(msg.from.id) : 'unknown';
    const text = safeString(msg.text || msg.caption || '');

    console.log(`✉ Received from ${userId} (${chatId}): ${text}`);

    // Quick guard: ignore empty
    if (!text.trim()) {
      return;
    }

    // Save incoming message to Supabase chat_history (best-effort)
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

    // Prepare OpenAI messages
    const userMessage = text;
    const messages = [
      { role: 'system', content: 'You are Mike, a helpful AI assistant for Pak Ya.' },
      { role: 'user', content: userMessage }
    ];

    // Call OpenAI
    let aiReply = 'Maaf Pak Ya, ada masalah teknikal. Sila cuba lagi.';
    try {
      const completion = await openai.chat.completions.create({
        model: OPENAI_MODEL,
        messages,
        max_tokens: 700,
      });

      // support different response shapes
      if (completion?.choices && completion.choices.length > 0) {
        const choice = completion.choices[0];
        aiReply = choice.message?.content ?? choice.text ?? aiReply;
      } else {
        console.warn('OpenAI returned empty choices:', completion);
      }
    } catch (e) {
      console.error('OpenAI error:', e.message || e);
    }

    // Send reply back to Telegram (best-effort, handle failures)
    try {
      await bot.sendMessage(chatId, aiReply, { parse_mode: 'HTML' });
    } catch (e) {
      console.error('Telegram sendMessage error:', e.message || e);
    }

    // Update last chat_history row with response (best-effort)
    try {
      if (supabase) {
        // update the latest record for this user (simple heuristic)
        const { data: rows } = await supabase
          .from('chat_history')
          .select('id')
          .eq('user_id', userId)
          .order('ts', { ascending: false })
          .limit(1);

        if (rows && rows.length > 0) {
          const rowId = rows[0].id;
          await supabase.from('chat_history').update({ response: aiReply }).match({ id: rowId });
        }
      }
    } catch (e) {
      console.error('Supabase update error (response):', e.message || e);
    }
  });

  bot.on('polling_error', (error) => {
    console.error('❗ Polling error:', error?.code ?? '', error?.message ?? error);
    // node-telegram-bot-api should restart polling automatically when { restart: true }
  });

  bot.on('webhook_error', (error) => {
    console.error('❗ Webhook error (unexpected):', error);
  });

  // keep alive logs
  setInterval(() => {
    console.log('⏱ heartbeat:', new Date().toISOString());
  }, 1000 * 60 * 5); // every 5 minutes
}

// global handlers
process.on('unhandledRejection', (reason) => {
  console.error('UnhandledRejection:', reason);
});
process.on('uncaughtException', (err) => {
  console.error('UncaughtException:', err);
  // give logs time to flush then exit so platform (Railway) restarts container
  setTimeout(() => process.exit(1), 1000);
});

startBot();
