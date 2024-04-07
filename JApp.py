from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import json

app = FastAPI()

# Enable CORS
origins = ["*"]  # Update with your actual frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
client = AsyncIOMotorClient('mongodb+srv://diwakar:yWwUI5qpupmNow1N@cluster0.de77o86.mongodb.net/')
db = client['scheme']
scheme_collection = db['scheme']
user_data_collection = db['user_data']

# Keywords representing states
state_keywords = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
                  "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
                  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
                  "Uttarakhand", "West Bengal"]

# Function to extract eligibility criteria and application process from scheme data
def extract_scheme_data(line):
    try:
        json_data = json.loads(line)
        props_data = json_data.get('props', {})
        page_props = props_data.get('pageProps', {})
        scheme_data = page_props.get('schemeData', {})
        en_data = scheme_data.get('en', {})
        eligibility_criteria = en_data.get('eligibilityCriteria')
        application_process = en_data.get('applicationProcess')

        if eligibility_criteria and application_process:
            return {'eligibilityCriteria': eligibility_criteria, 'applicationProcess': application_process}
    except json.JSONDecodeError:
        print(f'Invalid JSON format in line: {line}')
    return None

@app.get('/api/scheme-data')
async def get_scheme_data():
    scheme_data_list = []

    # Get all user data documents
    user_data_documents = await user_data_collection.find().to_list(length=None)

    for user_data in user_data_documents:
        user_city = user_data.get('city', '').strip()

        # Find schemes containing "props" in body_text
        results = await scheme_collection.find({'body_text': {'$regex': '.*props.*'}}).to_list(length=None)

        for result in results:
            body_text = result.get('body_text', [])
            for line in body_text:
                for keyword in state_keywords:
                    if keyword.lower() in line.lower():
                        # Matched a state keyword, check user's city
                        if user_city.lower() == keyword.lower():
                            scheme_data = extract_scheme_data(line)
                            if scheme_data:
                                scheme_data_list.append(scheme_data)

    # Return eligibilityCriteria and applicationProcess data as JSON response
    return scheme_data_list

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
