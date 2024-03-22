from flask import Flask, request, jsonify
import xmlrpc.client
from datetime import datetime, timedelta
import pytz
import phonenumbers

app = Flask(__name__)

def format_phone_number(phone):
    try:
        phone = ''.join(filter(str.isdigit, phone))
        
        if phone.startswith('0'):
            phone = phone[1:]

        if phone.startswith('55'):
            parsed_number = phonenumbers.parse(phone, 'BR')
            formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        else:
            formatted_phone = '55' + phone

        if formatted_phone.startswith('+'):
            formatted_phone = formatted_phone[1:]
        
        return formatted_phone
    except phonenumbers.phonenumberutil.NumberParseException:
        return None


def get_leads(id, limit, url, db, username, password):

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))

    uid = common.authenticate(db, username, password, {})

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    date_30_days_ago = datetime.now().astimezone(pytz.timezone('GMT')) - timedelta(days=30)
    print(date_30_days_ago)

    criteria = [
        ('write_date', '<', date_30_days_ago.strftime('%Y-%m-%d %H:%M:%S')),
        ('active', '=', False),
        ('lost_reason', '=', id),
        '|',
        ('phone', '!=', False),
        ('mobile', '!=', False),
    ]

    leads = models.execute_kw(db, uid, password, 'crm.lead', 'search_read', [criteria], {'fields': ['name', 'phone', 'mobile'], 'limit': limit})
    
    new_leads = []
    for lead in leads:
        if lead['mobile'] != False :
            phone_number = lead['mobile']
        else :
            phone_number = lead['phone']

        del lead['mobile']
        del lead['id']
        lead['phone'] = format_phone_number(phone_number)
        new_leads.append(lead)
            
    return new_leads

@app.route('/get_leads', methods=['POST'])
def get_leads_route():
    id = request.json.get('id')
    limit = request.json.get('limit')
    url = request.json.get('url')
    db = request.json.get('db')
    username = request.json.get('username')
    password = request.json.get('password')


    leads = get_leads(id, limit, url, db, username, password)
    return jsonify(leads)

if __name__ == '__main__':
    app.run(debug=True)