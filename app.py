from fastapi import FastAPI, Body, Depends, Query, Request
from fastapi.responses import JSONResponse
from db import *
from security import *
from sqlalchemy import func, alias


app = FastAPI()


@app.post("/login")
def login(email_id:str=Body(...),password:str=Body(...)):
    with database_client.Session() as session:
        employee_data = session.query(
            Employee
        ).filter(
            Employee.email_id == email_id
        ).first()

        if not employee_data:
            _content = {"meta":{"successful":False,"error":{"error_message":"invalid credentials"},},"data":None}
            return JSONResponse(status_code=403, content=_content)
        
        employee_data = employee_data.to_dict()

    _content, status_code = {"meta":{"successful":False,"error":{"error_message":"invalid credentials"},},"data":None}, 403
    if employee_data.get("password") == password:
        _token = generateJwtToken(exp=100000,user_id=employee_data.get("public_id"),company_id=employee_data.get("company",{}).get("public_id"),role_id=employee_data.get("role",{}).get("public_id"))
        _content, status_code = {"meta":{"successful":True,"error":None,"token":_token},"data":employee_data}, 200
    return JSONResponse(status_code=status_code, content=_content)
    

# Get Logs
@app.get("/logs")
def logs(*,
    company_id:str=Query(...), # all / company_id
    status_filter:str=Query(...), # success, all, failure, issue
    service_filter:str=Query(...), # face_comparison , all , passive_liveness
    start_datetime:datetime.datetime = Query(...),
    end_datetime:datetime.datetime = Query(...),
    page_no:int= Query(1),
    items_per_page:int= Query(15),
    decoded_token:dict = Depends(decodeJwtTokenDependancy),
    request:Request
):
    with database_client.Session() as session:

        log_data = session.query(
            FaceproofLogs,
        )

        if company_id != "all":
            log_data = log_data.join(Company, Company.company_id == FaceproofLogs.company_id).filter(Company.public_id == company_id)

        if status_filter != "all":
            log_data = log_data.join(
                StatusMaster,
                StatusMaster.status_id == FaceproofLogs.status_id
            ).filter(StatusMaster.status == status_filter.upper().strip())


        if service_filter != "all":
            log_data = log_data.join(
                ServiceMaster,
                ServiceMaster.service_id == FaceproofLogs.service_id
            ).filter(ServiceMaster.service_name == service_filter.upper().strip())


        log_data = log_data.filter(FaceproofLogs.create_date >= start_datetime,
                                FaceproofLogs.create_date <= end_datetime)
        
        
        total_count = log_data.with_entities(func.count()).scalar()

        # Pagination
        offset = (page_no - 1) * items_per_page
        log_data = log_data.offset(offset).limit(items_per_page)

        if log_data:
            log_data = log_data.all()
            log_data = [ ld.to_dict() for ld in log_data ]


    _content = {"meta":{"successful":True,"error":None,"pagination_data":{"items_per_page": items_per_page,"page_no": page_no,"total_count": total_count, "page_url": request.url._url}},"data":log_data}
    return JSONResponse(status_code=200, content=_content)


# Get Stats
@app.get("/logs_stats")
def logs(*,
    company_id:str=Query(...), # all / company_id
    # status_filter:str=Query(None), # success, all, failure, issue
    # service_filter:str=Query(None), # face_comparison , all , passive_liveness
    start_datetime:datetime.datetime = Query(...),
    end_datetime:datetime.datetime = Query(...),
    decoded_token:dict = Depends(decodeJwtTokenDependancy),
    request:Request
):
    with database_client.Session() as session:
        query = session.query(
            ServiceMaster.service_name,
            StatusMaster.status,
            # FaceproofLogs.service_id,
            # FaceproofLogs.service_id,
            func.count().label('count')
        ).join(
           FaceproofLogs,
           StatusMaster.status_id==FaceproofLogs.status_id
        ).join(
           ServiceMaster,
           ServiceMaster.service_id==FaceproofLogs.service_id
        )


        # Apply filters based on parameters
        if company_id != "all":
            query = query.join(Company, Company.company_id == FaceproofLogs.company_id).filter(Company.public_id == company_id)

        query = query.filter(FaceproofLogs.create_date >= start_datetime,
                                FaceproofLogs.create_date <= end_datetime)

        # Add grouping and ordering
        # query = query.group_by(FaceproofLogs.service_id, FaceproofLogs.status_id,)
        query = query.group_by(ServiceMaster.service_name, StatusMaster.status,)

        # subq_alias = alias(query)


        # q2 = session.query(
        #     StatusMaster.status,
        #     ServiceMaster.service_name,
        #     subq_alias.c.count
        # ).join(
        #     subq_alias,
        #     ServiceMaster.service_id==subq_alias.c.service_id
        # ).join(
        #    StatusMaster,
        #    StatusMaster.status_id==subq_alias.c.status_id 
        # )


        if query:
            query = query.all()
            nested_dict = {}
            for outer_key, inner_key, value in query:
                if outer_key not in nested_dict:
                    nested_dict[outer_key] = {}
                nested_dict[outer_key][inner_key] = value


    _content = {"meta":{"successful":True,"error":None},"data":nested_dict}
    return JSONResponse(status_code=200, content=_content)


# Get Invoice
# Get Invoice File


# Onboard Client
# CRUD Company
# CRUD Employee
# CRUD Billing


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0")