#!/bin/bash

# Get Chat ID helper script
BOT_TOKEN="8032450927:AAHYDEqnDu3AHG6HYHc8ud45NoD_0DLyp7o"

echo "🔍 Fetching recent Telegram bot updates..."
echo "📋 Make sure you've:"
echo "   1. Added @ChooseDaVibe_bot to your group"
echo "   2. Sent at least one message in the group"
echo ""

# Get updates and format nicely
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | jq -r '.result[] | "Chat ID: \(.message.chat.id) | Chat Title: \(.message.chat.title // .message.chat.first_name // "Private Chat") | Message: \(.message.text // .message.new_chat_member.first_name // "System Message")"'

echo ""
echo "💡 Copy the Chat ID number (including minus sign if present) and run:"
echo "   ./gradlew testTelegram -PchatId=\"CHAT_ID\""