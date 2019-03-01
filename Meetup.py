import requests
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
day_in_epochtime = 86400

MEETUP_API_KEY = config['DEFAULT']['MEETUP_API_KEY']
GMAIL_API_KEY = config['DEFAULT']['GMAIL_API_KEY']
RECIPIENT_EMAIL = config['DEFAULT']['RECIPIENT_EMAIL']
SENDER_EMAIL = config['DEFAULT']['SENDER_EMAIL']


class Meetup_Basketball(object):
    
    def __init__(self, events_already_sent):
        self.sent = events_already_sent

    def authorise_user(self, request):
        requests.get(request)        

    def get_events(self, request):
        send_request = requests.get(request)
        response = send_request.json()    
        return response

    def convert_time(epochtime):
        return time.strftime('%Y-%m-%d %H:%M:%S',
                             time.localtime(epochtime / 1000))
    """
    Each event is a result in the JSON Array
    """
    def get_events_for_next_week(self, response):
        upcoming_events = []        
        for event in range(len(response['results'])):
            epochtime = response['results'][event]['time']    
            if(epochtime / 1000 - time.time() < (day_in_epochtime * 14)):
                upcoming_events.append(response['results'][event])
        return upcoming_events

    def check_for_open_spots(self, upcoming_events):
        events_with_open_spots = []        
        for i in (upcoming_events):            
            going = i['yes_rsvp_count']
            event_limit = i['rsvp_limit']
            spots_available = event_limit - going            
            if spots_available > 0:
                print(spots_available)
                events_with_open_spots.append(i)
                self.check_if_already_notified(i)
        return events_with_open_spots

    def notify_user(self, event, payment_url):            
        print(' Sending email to user ...')        
        s = smtplib.SMTP('smtp.gmail.com', 587)        
        msg = MIMEMultipart()          
        s.starttls()
        s.login(SENDER_EMAIL, GMAIL_API_KEY)      
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = 'Meetup Spot Available - ' + event['name']
        message = 'Spot available ' + event['event_url'] + "\n" + payment_url
        msg.attach(MIMEText(message, 'plain'))
        s.send_message(msg)
        print("Email sent!")        

    """
    If user has already been notified for this event. Then leave them be.
    TODO: Add some logic, where just because the user has been notified before doesn't
    mean they shouldn't be again. Time or if a spot reopens. 
    """
    def check_if_already_notified(self, event):
        if event in self.sent:            
            print("User has already been notified for this event")
        else:            
            redirect_url = self.rsvp_to_event(event)
            self.notify_user(event, redirect_url)
    
    def rsvp_to_event(self, event):    
        print('RSVPing...')
        try:
            headers = {"content-type": "application/json"}
            event_id = event['id']
            params = {'event_id': event_id, 'agree_to_refund': 'true','rsvp': 'yes', 'key': MEETUP_API_KEY}
            rsvp = requests.post(url="https://api.meetup.com/2/rsvp", params=params)
            json_response = rsvp.json()
            print(json_response['payment_redirect'])   
            return(json_response['payment_redirect'])
        except:                        
            print("No spots open or exception thrown")

if __name__ == "__main__":    
    events_sent = []
    meetup = Meetup_Basketball(events_sent)
    user = meetup.authorise_user("https://secure.meetup.com/oauth2/authorize")    
    link = "https://api.meetup.com/2/events?&sign=true&photo-host=public&group_urlname=Manchester-Basketball-Meetup&page=20"
    response = meetup.get_events(link)
    upcoming_events = meetup.get_events_for_next_week(response)
    events_available = meetup.check_for_open_spots(upcoming_events)    