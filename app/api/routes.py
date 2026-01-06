from fastapi import APIRouter, UploadFile, File, Request, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import pandas as pd
from io import StringIO, BytesIO
import time

from app.crud import file_handler
from app.crud.openai import intent_prompt, insight_prompt, system_prompt, generate_prompt, analyze_intent, analyze_insight, combine_results

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
json_path = BASE_DIR / "lib" / "TEST_RES.json"
json_path_int = BASE_DIR / "lib" / "TEST_INTRES.json"
json_path_ins = BASE_DIR / "lib" / "TEST_INSRES.json"

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

ACTIVE_REPORT = {}

def block_if_report(request : Request):
    user_state = request.session.get("user_state",{})

    if user_state.get("report_active"):
        raise HTTPException(
            status_code=303,
            headers={
                "Location": f"/api/clean/{user_state['report_id']}"
            }
        )

#dependencies=[Depends(block_if_report)]
@router.get('/', response_class=HTMLResponse)
def index(request : Request):   
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@router.post('/upload', response_class=HTMLResponse)
async def upload_file(request : Request, file: UploadFile = File(...)):
    # validate file type
    if not file_handler.validate_file(file.filename.lower()):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error":"CSV or Excel file is only allowed."}
        )
    
    # read file to dataframe
    try:
        clean_id = await file_handler.read_validate_file(file)
        if clean_id is None:
            return templates.TemplateResponse("index.html",
                                              {"request": request, 
                                               "error": "File data structure is invalid."}
                                              )
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Failed to read file: {e}"})

    return RedirectResponse(url=f'/api/clean/{clean_id}', status_code=303)

@router.get('/clean/{clean_id}')
def clean(request : Request, clean_id : str):
    start = time.perf_counter()

    df = file_handler.load_file(clean_id)

    if df is None:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"File not found."})


    try:
        sum([i**2 for i in range(1000000)])

        # micro clean dataframe
        processed_df = file_handler.micro_clean(df)

        if processed_df.shape[0] > 25000:
            return templates.TemplateResponse("index.html", 
                                              {"request": request, 
                                               "error": f"Dataset is too large. Please upload a file with fewer than 10,000 rows."})
        
        # generate intent
        intent = generate_prompt(system_prompt(), intent_prompt(processed_df))
        intent_res = analyze_intent(processed_df, intent.choices[0].message.content)

        # generate insight
        insight = generate_prompt(system_prompt(), insight_prompt(intent_res))
        insight_res = analyze_insight(insight.choices[0].message.content)

        # combine intent and insight results
        combined_results = combine_results(intent_res, insight_res)

        end = time.perf_counter()
        duration = end - start

    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Something went wrong: {e}"})

    # set user session
    response.set_cookie(key="report_session", value=clean_id, httponly=True)

    ACTIVE_REPORT[clean_id] = {"status":"report generation", "start":time.time()}
    
    return templates.TemplateResponse(
        "report.html",
        {
            "request":request,
            "columns": list(processed_df.columns),
            "dtypes":processed_df.dtypes,
            "rows": processed_df.to_dict("records"),
            "openai_response": combined_results,
            "success":"Data is successfully analyzed.",
            "runtime":round(duration,2),
            "intent":intent_res
        }
    )

@router.get('/quit_report', response_class=HTMLResponse)
async def quit_report(request : Request):
    request.session["user_state"] = {
        "report_active": False,
        "report_id": None
    }

    return RedirectResponse(url='/api', status_code=303)


@router.get('/logout')
def logout(response: Response):
    response.delete_cookie("report_id")
    return {"message": "session removed"}