from fastapi import FastAPI, Depends, Query, Path
from pymongo import MongoClient
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# Connect to MongoDB
# client = MongoClient('mongodb://localhost:27017')
client = MongoClient('mongodb+srv://diwakar:yWwUI5qpupmNow1N@cluster0.de77o86.mongodb.net/')
db = client['scheme']
scheme_collection = db['scheme']
user_data_collection = db['user_data']

# Keywords representing states
state_keywords = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal"
]

# Models for request and response data
class UserCity(BaseModel):
    city: Optional[str] = None

class SchemeData(BaseModel):
    eligibilityCriteria: str
    applicationProcess: str

@app.get("/api/scheme-data", summary="Get scheme data based on user location")
async def get_scheme_data(
    user_city: UserCity = Depends(Query("city", nullable=True, description="User's city")),
):
    # Retrieve user data based on provided city
    user_data = user_data_collection.find_one({"city": user_city.city.lower()})

    if not user_data:
        # No user data found with given city
        return {"message": "No user data found with provided city."}

    # Find schemes containing "props" in body_text and matching user's state
    results = scheme_collection.find({
        "body_text": {"$regex": ".*props.*"},
        "body_text": {"$regex": f".*{user_city.city.lower()}", "$options": "i"}
    })

    scheme_data_list = []
    for result in results:
        body_text = result.get("body_text", [])
        for line in body_text:
            try:
                json_data = json.loads(line)
                props_data = json_data.get("props", {})
                page_props = props_data.get("pageProps", {})
                scheme_data = page_props.get("schemeData", {})
                en_data = scheme_data.get("en", {})
                eligibility_criteria = en_data.get("eligibilityCriteria")
                application_process = en_data.get("applicationProcess")

                if eligibility_criteria and application_process:
                    scheme_data_list.append(SchemeData(eligibilityCriteria=eligibility_criteria, applicationProcess=application_process))
            except json.JSONDecodeError:
                print(f"Invalid JSON format in line: {line}")
                continue

    return scheme_data_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
