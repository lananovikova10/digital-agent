#!/bin/bash

BOT_TOKEN="8032450927:AAHYDEqnDu3AHG6HYHc8ud45NoD_0DLyp7o"
BASE_URL="https://api.telegram.org/bot${BOT_TOKEN}"

echo "🤖 TELEGRAM BOT DEBUGGING TOOL"
echo "================================"
echo ""

echo "1️⃣ Bot Information:"
curl -s "${BASE_URL}/getMe" | jq -r '.result | "Bot Name: \(.first_name) (@\(.username // "no username"))\nBot ID: \(.id)\nCan Join Groups: \(.can_join_groups)\nCan Read All Group Messages: \(.can_read_all_group_messages)"'
echo ""

echo "2️⃣ Webhook Status:"
curl -s "${BASE_URL}/getWebhookInfo" | jq -r '.result | "Webhook URL: \(.url // "Not set")\nPending Updates: \(.pending_update_count)"'
echo ""

echo "3️⃣ Recent Updates (last 24 hours):"
UPDATES=$(curl -s "${BASE_URL}/getUpdates?offset=0&limit=100")
UPDATE_COUNT=$(echo "$UPDATES" | jq '.result | length')
echo "Found $UPDATE_COUNT updates"

if [ "$UPDATE_COUNT" -gt 0 ]; then
    echo "$UPDATES" | jq -r '.result[] | "─────────────────────────────────────\nUpdate ID: \(.update_id)\nChat ID: \(.message.chat.id // .my_chat_member.chat.id // "Unknown")\nChat Type: \(.message.chat.type // .my_chat_member.chat.type // "Unknown")\nChat Title: \(.message.chat.title // .my_chat_member.chat.title // .message.chat.first_name // "No title")\nMessage: \(.message.text // .my_chat_member.new_chat_member.status // "System message")\nDate: \(.message.date // .my_chat_member.date // "Unknown") (\((.message.date // .my_chat_member.date // 0) | strftime("%Y-%m-%d %H:%M:%S")))"'
else
    echo "❌ No updates found!"
    echo ""
    echo "🔍 TROUBLESHOOTING STEPS:"
    echo "========================"
    echo "1. Open Telegram on your phone/computer"
    echo "2. Search for: @ChooseDaVibe_bot"
    echo "3. Start a conversation by clicking 'START' or sending '/start'"
    echo "4. Send any message like 'Hello'"
    echo "5. Run this script again"
    echo ""
    echo "OR for group chats:"
    echo "1. Add @ChooseDaVibe_bot to your group"
    echo "2. Send any message in the group"
    echo "3. Run this script again"
    echo ""
    echo "🤖 Bot link: https://t.me/ChooseDaVibe_bot"
fi

echo ""
echo "4️⃣ Testing message send to a sample chat ID:"
echo "If you know your chat ID, you can test directly:"
echo "   ./gradlew testTelegram -PchatId=\"YOUR_CHAT_ID\""
echo ""
echo "Common chat ID formats:"
echo "   Personal chat: positive number (e.g., 123456789)"
echo "   Group chat: negative number (e.g., -1001234567890)"