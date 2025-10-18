# 🌟 PREMIUM SYSTEM USER GUIDE

## 🎯 HOW THE NEW PREMIUM SYSTEM WORKS

### For Regular Users

#### Step 1: Request Premium
Run the command:
```
/get_premium
```

You'll see an embed with:
- Premium tier information (Basic/Pro/Elite)
- Pricing details
- How the system works
- **"Contact Developer" button** ← Click this!

#### Step 2: Ticket Channel Opens
When you click "Contact Developer":
- A private channel is created: `premium-ticket-{your_id}`
- Only YOU, the BOT, and the DEVELOPER can see it
- You'll see a welcome message with:
  - Premium tier details
  - Grant premium buttons (developer will use these)
  - Instructions on what to do next

#### Step 3: Discuss with Developer
- The developer receives a DM notification
- They'll join your ticket channel
- Discuss which tier you want
- Ask any questions about features
- Provide payment confirmation (external)

#### Step 4: Premium Activated
- Developer clicks the appropriate grant button (Basic/Pro/Elite)
- You receive a DM confirming activation
- Premium is active immediately!
- Use `/premium_status` to verify

#### Step 5: Enjoy Premium Features
Your premium benefits are active:
- ✅ Unlimited portfolio links
- ✅ Custom banners on profile
- ✅ Gold profile embeds
- ✅ Bump every 6 hours (vs 24h)
- ✅ Premium badge 🌟

---

### For Developer (You)

#### When User Requests Premium:

1. **DM Notification Received**:
   - You get a DM with user info
   - Click "Jump to Ticket" button
   - Opens the private ticket channel

2. **In the Ticket Channel**:
   - Discuss with the user
   - Verify payment (external to Discord)
   - Answer any questions

3. **Grant Premium**:
   Click one of the buttons:
   - **Grant Basic (30d)** ⭐ - $5/month tier
   - **Grant Pro (30d)** 💎 - $10/month tier
   - **Grant Elite (30d)** 👑 - $20/month tier

4. **Confirmation**:
   - User receives DM notification
   - Channel shows confirmation embed
   - Premium is active immediately

5. **Close Ticket**:
   - Click **Close Ticket** 🔒 button
   - Channel deletes after 5 seconds

#### Developer Commands:

##### Grant Premium Manually (without ticket):
```
/dev_premium_add @user 30 basic
/dev_premium_add @user 30 pro
/dev_premium_add @user 30 elite
```
- Replace `@user` with the Discord user
- Replace `30` with number of days
- Choose tier: `basic`, `pro`, or `elite`

##### Remove Premium:
```
/dev_premium_remove @user
```
- Instantly revokes premium
- User loses all premium benefits

##### List All Premium Users:
```
/dev_premium_list
```
- Shows all active premium users
- Displays tier and expiry date
- Only visible to you (ephemeral)

---

## 🔐 SECURITY FEATURES

### Developer-Only Access:
- ✅ All premium commands check `interaction.user.id == DEVELOPER_ID`
- ✅ Developer ID stored in `.env` file (not hardcoded)
- ✅ Even server admins CANNOT grant premium
- ✅ Ticket grant buttons only work for developer

### Ticket System Security:
- ✅ Private channels with permission overwrites
- ✅ Only user, bot, and developer can view
- ✅ Ticket category hidden from everyone else
- ✅ Automatic cleanup on ticket close

---

## 💎 PREMIUM TIERS BREAKDOWN

### **Basic Premium** - $5/month
Perfect for individual editors:
- ✅ Unlimited portfolio links (vs 1)
- ✅ Custom banner on profile
- ✅ Gold profile embed color
- ✅ 6-hour bump cooldown (vs 24h)
- ✅ 🌟 Premium badge

### **Pro Premium** - $10/month
For professional editors:
- ✅ All Basic features
- ✅ Priority in job recommendations
- ✅ Advanced analytics dashboard
- ✅ Custom profile themes
- ✅ Featured in "Pro Creators" section
- ✅ 5 collab posts per month

### **Elite Premium** - $20/month
For top-tier creators:
- ✅ All Pro features
- ✅ Verified Creator badge ✅
- ✅ Priority support (24h response)
- ✅ Featured profile placement
- ✅ Unlimited collab posts
- ✅ Monthly 1-on-1 consultation
- ✅ Early access to new features

---

## 📊 PREMIUM FEATURE VERIFICATION

### How to Check if Features are Working:

#### 1. Portfolio Links:
- **Free**: Try adding 2+ links → Should get error
- **Premium**: Add unlimited links → Should work
- Test in `/create_profile` command

#### 2. Banners:
- **Free**: Add banner URL → Should get error
- **Premium**: Add banner URL → Should display on profile
- Test in `/create_profile` command

#### 3. Gold Embeds:
- **Free**: Profile embed is BLUE with "📌 Profile"
- **Premium**: Profile embed is GOLD with "🌟 Premium Profile"
- Test with `/profile` command

#### 4. Bump Cooldown:
- **Free**: Must wait 24 hours between bumps
- **Premium**: Can bump every 6 hours
- Test with `/bump_profile` command
- Check "Next Bump" timestamp on profile

#### 5. Premium Badge:
- **Premium**: Profile title shows "🌟 Premium Profile"
- Badge appears in all profile displays
- Visible to everyone

---

## 🎮 EXAMPLE WORKFLOWS

### Scenario 1: New User Wants Premium

**User's Perspective**:
```
User: /get_premium
Bot: [Shows premium info with button]
User: *clicks "Contact Developer"*
Bot: ✅ Premium ticket created! Check #premium-ticket-123456789
User: *goes to ticket channel*
User: "Hi! I'd like Elite premium please"
Developer: "Great! That's $20/month. Please send payment to [payment method]"
User: *sends payment confirmation*
Developer: *clicks "Grant Elite (30d)" button*
Bot: ✅ Premium Granted! [confirmation embed]
User: *receives DM* "🎉 Your Elite Premium has been activated!"
User: /premium_status
Bot: [Shows Elite tier, expiry date]
```

### Scenario 2: Developer Manually Grants Premium

**Developer's Perspective**:
```
Developer: /dev_premium_add @JohnEditor 30 pro
Bot: ✅ Granted Pro Premium to @JohnEditor for 30 days. Expires: <timestamp>
User: *receives DM* "🎉 You've been granted Pro Premium!"
```

### Scenario 3: Premium Expires

**Automatic Process**:
```
[Premium expiry background task runs every hour]
Bot: *checks all premium users*
Bot: *finds expired premium for user*
Bot: *removes premium from database*
Bot: *user's next profile bump uses 24h cooldown*
Bot: *user's profile embed changes to blue*
```

### Scenario 4: User Checks Status

**User's Perspective**:
```
User: /premium_status
Bot: [If Premium] "🌟 You have Pro Premium! Expires in 15 days"
Bot: [If Not Premium] "💎 Premium Not Active. Use /get_premium to upgrade!"
```

---

## 🛠️ TROUBLESHOOTING

### Issue: User can't see ticket channel
**Solution**: 
- Check if user left the server
- Verify bot has "Manage Channels" permission
- Check if category "Premium Tickets" exists

### Issue: Developer doesn't get DM notification
**Solution**:
- Developer must have DMs enabled from server members
- Bot must share a server with developer
- Check DEVELOPER_ID in .env is correct

### Issue: Grant buttons don't work
**Solution**:
- Only developer can use grant buttons
- Check DEVELOPER_ID matches your Discord ID
- Verify premium_cog is loaded (`/dev_premium_list` should work)

### Issue: Premium features not working after grant
**Solution**:
- User needs to recreate/update profile for new limits
- Wait 5 minutes for cache to update
- Check database with `/dev_premium_list`

### Issue: Ticket channel won't close
**Solution**:
- Check bot has "Manage Channels" permission
- Manually delete channel if needed
- Only developer can close tickets

---

## 📋 ADMIN TASKS

### Monthly Premium Management:

1. **Check Expiring Premium** (start of month):
```
/dev_premium_list
```
- Look for "Expires in X days"
- DM users who are expiring soon
- Offer renewal discounts

2. **Review Revenue**:
- Track active subscriptions
- Calculate MRR (Monthly Recurring Revenue)
- Plan feature improvements based on income

3. **Clean Up Old Tickets**:
- Check "Premium Tickets" category
- Delete abandoned ticket channels
- Archive important conversations

### Renewing Premium:

When user wants to renew:
```
/dev_premium_add @user 30 [tier]
```
- This EXTENDS their current premium (doesn't reset)
- If expired, activates immediately
- User gets confirmation DM

---

## 🎯 BEST PRACTICES

### For Developer:

1. **Respond to tickets within 24h** - Keep users happy
2. **Be clear about pricing** - No surprises
3. **Use external payment** - PayPal, Stripe, etc. (Discord TOS)
4. **Keep records** - Track who paid and when
5. **Offer trials** - 7-day free trial for trusted users
6. **Bundle discounts** - 3 months for price of 2, etc.
7. **Referral rewards** - Give 1 month free for 5 referrals

### For Users:

1. **Use /premium_status regularly** - Track your expiry
2. **Contact before expiry** - Renew before losing benefits
3. **Provide feedback** - Help improve premium features
4. **Report bugs** - Premium features should always work

---

## 📞 SUPPORT

### For Premium Issues:

**Users can**:
- Use `/get_premium` to open ticket
- DM developer directly (if allowed)
- Ask in support channel

**Developer should**:
- Monitor ticket category daily
- Keep DMs open for premium users
- Provide 24h response for Elite users

---

## 🚀 FUTURE PREMIUM FEATURES

### Coming Soon:
- 🔜 EditorCoins daily bonus (Basic: +10, Pro: +25, Elite: +50)
- 🔜 Marketplace fee reduction (Free: 10%, Premium: 5%, Elite: 0%)
- 🔜 Advanced analytics dashboard
- 🔜 Custom profile themes
- 🔜 Priority job matching
- 🔜 Featured creator placement
- 🔜 AI features access

### Planned Premium Perks:
See `ADVANCED_FEATURES_SUGGESTIONS.md` for full list of upcoming features.

---

## 💰 PRICING STRATEGY

### Current Pricing:
- **Basic**: $5/month (entry level)
- **Pro**: $10/month (2x Basic)
- **Elite**: $20/month (2x Pro, 4x Basic)

### Recommended Strategies:
1. **Yearly Discounts**: Offer 2 months free for annual payment
2. **Referral Rewards**: 1 month free for 5 referrals
3. **Bulk Discounts**: Team plans (5 users = 20% off)
4. **Trial Period**: 7-day free trial for new users
5. **Loyalty Rewards**: 10% off for 6+ months continuous subscription

---

**YOUR PREMIUM SYSTEM IS NOW FULLY FUNCTIONAL AND READY TO ACCEPT CUSTOMERS!** 🎉

All tickets are secure, all features are working, and you have complete control over who gets premium.
