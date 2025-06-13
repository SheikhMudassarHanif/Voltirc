# from twilio.rest import Client

# # Twilio credentials
# account_sid = "ACcb33680cd74385251c187ef3ae745bdc"
# # ACcb33680cd74385251c187ef3ae745bdc
# auth_token = "0b786d3fe497bdf23f0d423ef46f7427"

# # Initialize the Twilio client
# client = Client(account_sid, auth_token)

# # Phone numbers
# from_number = "+14155238886"        # Your Twilio number
# to_number = "+923059743254"         # Replace with your phone number

# # Send the message
# message = client.messages.create(
#     body="✅ Hello from your Twilio bot!",
#     from_=from_number,
#     to=to_number
# )

# print(f"✅ Message sent! SID: {message.sid}")


from twilio.rest import Client

account_sid = "ACcb33680cd74385251c187ef3ae745bdc"
auth_token = "105bb238ff519c37ad48df3373cbc576"
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  body='Your appointment is coming up on July 21 at 3PM',
  to='whatsapp:+923059743254'
)

print(message.sid)



# from twilio.rest import Client

# account_sid = 'ACcb33680cd74385251c187ef3ae745bdc'
# auth_token = '[AuthToken]'
# client = Client(account_sid, auth_token)

# message = client.messages.create(
#   from_='whatsapp:+14155238886',
#   content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
#   content_variables='{"1":"12/1","2":"3pm"}',
#   to='whatsapp:+923059743254'
# )

# print(message.sid)