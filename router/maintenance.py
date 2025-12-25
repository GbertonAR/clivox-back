"""
ACS Maintenance Router - Hidden endpoints for database cleanup and maintenance tasks.
"""
from fastapi import APIRouter, Header, HTTPException
from datetime import datetime, timedelta
import sqlite3
import os

router = APIRouter(prefix="/admin/maintenance", tags=["maintenance"])

DB_PATH = "clivox.db"
MAINTENANCE_SECRET = os.getenv("MAINTENANCE_SECRET", "clivox-maint-2024")


def verify_secret(x_maintenance_secret: str = Header(None)):
    """Verify maintenance secret header for protected endpoints."""
    if x_maintenance_secret != MAINTENANCE_SECRET:
        raise HTTPException(status_code=403, detail="Invalid maintenance secret")
    return True


@router.post("/cleanup/llamada-eventos")
def cleanup_llamada_eventos(
    days_to_keep: int = 7,
    x_maintenance_secret: str = Header(None)
):
    """
    Clean old records from llamada_eventos table.
    Keeps only records from the last N days.
    """
    verify_secret(x_maintenance_secret)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get count before cleanup
    cursor.execute("SELECT COUNT(*) FROM llamada_eventos")
    count_before = cursor.fetchone()[0]
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    # Delete old records
    cursor.execute(
        "DELETE FROM llamada_eventos WHERE timestamp < ?",
        (cutoff_date.isoformat(),)
    )
    deleted_count = cursor.rowcount
    
    conn.commit()
    
    # Get count after cleanup
    cursor.execute("SELECT COUNT(*) FROM llamada_eventos")
    count_after = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "status": "success",
        "table": "llamada_eventos",
        "records_before": count_before,
        "records_deleted": deleted_count,
        "records_after": count_after,
        "cutoff_date": cutoff_date.isoformat(),
        "days_kept": days_to_keep
    }


@router.post("/cleanup/sala-estado")
def cleanup_sala_estado(x_maintenance_secret: str = Header(None)):
    """
    Reset sala_estado table - clears all participant data and whiteboard states.
    Use this when no active calls are happening.
    """
    verify_secret(x_maintenance_secret)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get count before cleanup
    cursor.execute("SELECT COUNT(*) FROM sala_estado")
    count_before = cursor.fetchone()[0]
    
    # Reset all sala_estado records to empty state
    cursor.execute("""
        UPDATE sala_estado 
        SET whiteboard_data = '[]', 
            participantes_activos = '[]',
            last_updated = ?
    """, (datetime.utcnow(),))
    updated_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "table": "sala_estado",
        "records_reset": updated_count,
        "message": "All sala_estado records reset to empty state"
    }


@router.post("/cleanup/all")
def cleanup_all(
    days_to_keep: int = 7,
    x_maintenance_secret: str = Header(None)
):
    """
    Run all cleanup operations at once.
    """
    verify_secret(x_maintenance_secret)
    
    results = {
        "llamada_eventos": cleanup_llamada_eventos(days_to_keep, x_maintenance_secret),
        "sala_estado": cleanup_sala_estado(x_maintenance_secret),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return results


@router.get("/stats")
def get_maintenance_stats(x_maintenance_secret: str = Header(None)):
    """
    Get current database statistics for maintenance planning.
    """
    verify_secret(x_maintenance_secret)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # llamada_eventos stats
    cursor.execute("SELECT COUNT(*) FROM llamada_eventos")
    stats["llamada_eventos_total"] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT evento, COUNT(*) 
        FROM llamada_eventos 
        GROUP BY evento
    """)
    stats["llamada_eventos_by_type"] = dict(cursor.fetchall())
    
    cursor.execute("""
        SELECT MIN(timestamp), MAX(timestamp) 
        FROM llamada_eventos
    """)
    row = cursor.fetchone()
    stats["llamada_eventos_date_range"] = {
        "oldest": row[0],
        "newest": row[1]
    }
    
    # sala_estado stats
    cursor.execute("SELECT COUNT(*) FROM sala_estado")
    stats["sala_estado_total"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT sala_id, last_updated FROM sala_estado")
    stats["sala_estado_rooms"] = [
        {"sala_id": r[0], "last_updated": r[1]} 
        for r in cursor.fetchall()
    ]
    
    conn.close()
    
    return stats
