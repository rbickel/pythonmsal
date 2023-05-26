from flask import Flask, jsonify, request
import msal 
import config2 as cfg
import pandas as pd
import os 
import http.client
import json
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
is_deployed_in_azure = 1

@app.route('/user/<user_email>', methods=['GET'])
def get_markets_from_user(user_email):
    # your existing code goes here...
    user_email = user_email.upper()
    print('USER_EMAIL:', user_email)

    is_hq = False

    if cfg.USE_AZURE_AD_GROUPS_SECURITY:

        
            if '@GIONITA.RO' in user_email:
                authority = cfg.AD_AUTHORITY.replace("organizations", cfg.AD_TENANT_ID)
               
                clientapp = msal.ConfidentialClientApplication(
                    cfg.AD_CLIENT_ID,
                    client_credential=cfg.AD_CLIENT_SECRET,
                    authority=authority,
                    azure_region= 'None',
                    
                )
               
                # Make a client call if Access token is not available in cache
                response = clientapp.acquire_token_for_client(scopes=cfg.AD_SCOPE)
                print(response)
                #response1 = clientapp.acquire_token_silent(scopes=cfg.AD_SCOPE, account=user_email, force_refresh=True)
                access_token = response["access_token"] 
                

                headers = {
                    'Content-Type': "application/json",
                    'Authorization': 'Bearer {}'.format(access_token)
                }
                conn = http.client.HTTPSConnection('graph.microsoft.com')
                request = f'/v1.0/{cfg.AD_TENANT_ID}/users/{user_email}/memberOf'
                retrieved_all_pages = False
                groups_from_user = pd.DataFrame(columns=['id', 'displayName'])

                while not retrieved_all_pages:
                    conn.request("GET", request, "", headers)
                    response = conn.getresponse()
                    data = response.read()
                    data = json.loads(data)

                    if 'value' in data.keys():
                        data_df = pd.DataFrame(data['value'])[['id', 'displayName']]
                        groups_from_user = pd.concat([groups_from_user, data_df], ignore_index=True)
                        if '@odata.nextLink' in list(data.keys()):
                            request = data['@odata.nextLink']
                        else:
                            retrieved_all_pages = True

                    else:
                        retrieved_all_pages = True
                conn.close()

                groups_from_user['displayName'] = groups_from_user['displayName'].str.upper()

                print(groups_from_user['displayName'].tolist())

    
    # at the end return JSON response
    
    return jsonify(groups=groups_from_user.to_dict(orient='records'), is_hq=is_hq)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
