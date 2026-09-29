module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).send('Method Not Allowed');

  if (req.headers['x-telegram-bot-api-secret-token'] !== process.env.TELEGRAM_WEBHOOK_SECRET) {
    return res.status(401).send('Unauthorized');
  }

  const cb = req.body && req.body.callback_query;
  if (!cb) return res.status(200).send('ignored');

  const [action, phone] = (cb.data || '').split(':');
  const botToken = process.env.TELEGRAM_BOT_TOKEN;

  const answer = (text) => fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ callback_query_id: cb.id, text })
  });

  const editMessage = (newText) => fetch(`https://api.telegram.org/bot${botToken}/editMessageText`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: cb.message.chat.id,
      message_id: cb.message.message_id,
      text: newText
    })
  });

  if (!phone) {
    await answer('خطأ: بيانات ناقصة');
    return res.status(200).send('ok');
  }

  try {
    if (action === 'approve') {
      const code = Math.random().toString(36).substring(2, 10);
      const sbRes = await fetch(
        `${process.env.SUPABASE_URL}/rest/v1/technicians?phone=eq.${encodeURIComponent(phone)}`,
        {
          method: 'PATCH',
          headers: {
            apikey: process.env.SUPABASE_SECRET_KEY,
            Authorization: `Bearer ${process.env.SUPABASE_SECRET_KEY}`,
            'Content-Type': 'application/json',
            Prefer: 'return=representation'
          },
          body: JSON.stringify({ approved: true, code })
        }
      );
      const data = await sbRes.json();
      if (!sbRes.ok || !data.length) {
        await answer('فشل: ما لقيتش الحرفي');
      } else {
        await answer('تمت الموافقة ✅');
        await editMessage(`${cb.message.text}\n\n✅ تمت الموافقة — الكود: ${code}`);
      }
    } else if (action === 'reject') {
      await answer('تم الرفض ❌');
      await editMessage(`${cb.message.text}\n\n❌ تم الرفض`);
    } else {
      await answer('حاجة غير معروفة');
    }
  } catch (err) {
    console.error(err.message);
    await answer('خطأ تقني');
  }

  return res.status(200).send('ok');
};
