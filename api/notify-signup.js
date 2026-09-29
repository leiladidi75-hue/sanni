module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).send('Method Not Allowed');
  }

  const secret = req.headers['x-webhook-secret'];
  if (secret !== process.env.WEBHOOK_SECRET) {
    return res.status(401).send('Unauthorized');
  }

  const record = req.body && req.body.record;
  if (!record) {
    return res.status(400).send('No record in payload');
  }

  const name = record.name || 'غير معروف';
  const phone = record.phone || 'غير معروف';
  const text = `🔔 تسجيل حرفي جديد\nالاسم: ${name}\nالهاتف: ${phone}`;

  try {
    await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: process.env.TELEGRAM_CHAT_ID,
        text,
        reply_markup: {
          inline_keyboard: [[
            { text: '✅ موافقة', callback_data: `approve:${phone}` },
            { text: '❌ رفض', callback_data: `reject:${phone}` }
          ]]
        }
      })
    });
    return res.status(200).send('OK');
  } catch (err) {
    console.error('Telegram error:', err.message);
    return res.status(500).send('Failed');
  }
};
