from fastapi import HTTPException
def validate_final_score(score_type: str, score: str):
    if score_type == "color" and score not in ["green", "yellow", "red"]:
        raise HTTPException(status_code=400, detail="Invalid color score")
    elif score_type == "yes_no" and score not in ["yes", "no"]:
        raise HTTPException(status_code=400, detail="Invalid yes/no score")
    elif score_type == "scale":
        try:
            val = int(score)
            if val < 1 or val > 10:
                raise HTTPException(status_code=400, detail="Scale score must be between 1 and 10")
        except ValueError:
            raise HTTPException(status_code=400, detail="Scale score must be an integer")
