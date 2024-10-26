from pydantic import BaseModel

class BPU(BaseModel):
    nombre_agents: list[int] 
    nombre_cdi: list[int] 
    nombre_cdd: list[int] 
    autres_details: list[str] 