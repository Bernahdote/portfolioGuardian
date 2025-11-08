import smtplib

def send_message(recipient, message, password, subject="",):
    email = "teo-portfolioGuardian"

    auth = (email, password)

    headers = f"From: {auth[0]}\r\nTo: {recipient}\r\nSubject: {subject}\r\n"
    body = message


    headers_encoded = headers.encode('utf-8')
    body_encoded = body.encode('utf-8')

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(auth[0], auth[1])

        server.sendmail(auth[0], recipient, headers_encoded + b'\r\n' + body_encoded)
