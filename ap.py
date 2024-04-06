 
from flask import Flask, jsonify
from pymongo import MongoClient
import json
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
# client = MongoClient('mongodb://localhost:27017')
mongo_connection_string = os.environ.get('MONGO_CONNECTION_STRING')

client = MongoClient(mongo_connection_string)
db = client['scheme']
scheme_collection = db['scheme']
user_data_collection = db['user_data']

# Keywords representing states
state_keywords = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
                  "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
                  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
                  "Uttarakhand", "West Bengal"]

@app.route('/api/scheme-data', methods=['GET'])
def get_scheme_data():
    # Get all user data documents
    user_data_documents = user_data_collection.find()

    # Store eligibilityCriteria and applicationProcess data from props for documents with matched keywords in body_text
    scheme_data_list = []

    for user_data in user_data_documents:
        user_city = user_data.get('city', '').strip()

        # Find schemes containing "props" in body_text
        results = scheme_collection.find({'body_text': {'$regex': '.*props.*'}})

        for result in results:
            body_text = result.get('body_text', [])
            for line in body_text:
                for keyword in state_keywords:
                    if keyword.lower() in line.lower():
                        # Matched a state keyword, check user's city
                        if user_city.lower() == keyword.lower():
                            try:
                                json_data = json.loads(line)
                                props_data = json_data.get('props', {})
                                page_props = props_data.get('pageProps', {})
                                scheme_data = page_props.get('schemeData', {})
                                en_data = scheme_data.get('en', {})
                                eligibility_criteria = en_data.get('eligibilityCriteria')
                                application_process = en_data.get('applicationProcess')

                                if eligibility_criteria and application_process:
                                    scheme_data_list.append({'eligibilityCriteria': eligibility_criteria, 'applicationProcess': application_process})
                            except json.JSONDecodeError:
                                print(f'Invalid JSON format in line: {line}')
                                continue

    # Return eligibilityCriteria and applicationProcess data as JSON response
    return jsonify(scheme_data_list)

if __name__ == '__main__':
    app.run(debug=True)
