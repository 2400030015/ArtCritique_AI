import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "art_critique.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    """Initializes the SQLite database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)

    # Create Artworks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            image_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Create Analysis table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis (
            artwork_id INTEGER PRIMARY KEY,
            composition_score REAL NOT NULL,
            color_score REAL NOT NULL,
            contrast_score REAL NOT NULL,
            aesthetic_score REAL NOT NULL,
            symmetry_score REAL NOT NULL,
            balance_score REAL NOT NULL,
            visual_appeal_score REAL NOT NULL,
            professional_quality_score REAL NOT NULL,
            style TEXT NOT NULL,
            verdict TEXT NOT NULL,
            FOREIGN KEY (artwork_id) REFERENCES artworks(id) ON DELETE CASCADE
        )
    """)

    # Create AI Feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_feedback (
            artwork_id INTEGER PRIMARY KEY,
            strengths TEXT NOT NULL,  -- JSON string of list
            weaknesses TEXT NOT NULL, -- JSON string of list
            suggestions TEXT NOT NULL, -- JSON string of list
            insights TEXT NOT NULL,
            roadmap_immediate TEXT NOT NULL, -- JSON string of list
            roadmap_longterm TEXT NOT NULL,  -- JSON string of list
            style_percentages TEXT NOT NULL, -- JSON string of dict
            FOREIGN KEY (artwork_id) REFERENCES artworks(id) ON DELETE CASCADE
        )
    """)

    # Create Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artwork_id INTEGER NOT NULL,
            pdf_path TEXT NOT NULL,
            FOREIGN KEY (artwork_id) REFERENCES artworks(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    seed_default_user()

def seed_default_user():
    """Seeds a default guest user so the app is immediately usable."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Guest Artist", "guest@artcritique.ai")
        )
        conn.commit()
    conn.close()

def cleanup_broken_records():
    """Detects broken image paths and deletes those records from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cleaned_count = 0
    try:
        cursor.execute("SELECT id, image_path FROM artworks")
        rows = cursor.fetchall()
        
        broken_ids = []
        for row in rows:
            art_id = row["id"]
            img_path = row["image_path"]
            if not img_path or not os.path.exists(img_path):
                broken_ids.append(art_id)
                
        if broken_ids:
            # Delete broken records. PRAGMA foreign_keys = ON automatically cascade-deletes children!
            cursor.executemany("DELETE FROM artworks WHERE id = ?", [(art_id,) for art_id in broken_ids])
            conn.commit()
            cleaned_count = len(broken_ids)
            print(f"Database cleanup: Removed {cleaned_count} records with missing images.")
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()
    return cleaned_count

def save_analysis(user_id, title, image_path, metrics, feedback):
    """
    Saves the artwork metadata, opencv analysis, and Gemini AI feedback.
    
    Parameters:
    - user_id: ID of the user uploading the art.
    - title: Title of the artwork.
    - image_path: Path where the image is stored.
    - metrics: Dict with composition, color, contrast, symmetry, balance.
    - feedback: Dict containing Gemini response (strengths, weaknesses, visual appeal, style percentages, etc.)
    
    Returns:
    - artwork_id: ID of the newly created artwork record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Insert Artwork
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO artworks (user_id, title, image_path, created_at) VALUES (?, ?, ?, ?)",
            (user_id, title, image_path, created_at)
        )
        artwork_id = cursor.lastrowid

        # 2. Insert Analysis Metrics
        cursor.execute("""
            INSERT INTO analysis (
                artwork_id, composition_score, color_score, contrast_score, aesthetic_score,
                symmetry_score, balance_score, visual_appeal_score, professional_quality_score, style, verdict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artwork_id,
            metrics.get("composition_score", 0.0),
            metrics.get("color_score", 0.0),
            metrics.get("contrast_score", 0.0),
            feedback.get("aesthetic_score", 0.0),
            metrics.get("symmetry_score", 0.0),
            metrics.get("balance_score", 0.0),
            feedback.get("visual_appeal_score", 0.0),
            feedback.get("professional_quality_score", 0.0),
            feedback.get("style", "Unknown"),
            feedback.get("verdict", "Beginner")
        ))

        # 3. Insert AI Feedback
        cursor.execute("""
            INSERT INTO ai_feedback (
                artwork_id, strengths, weaknesses, suggestions, insights,
                roadmap_immediate, roadmap_longterm, style_percentages
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artwork_id,
            json.dumps(feedback.get("strengths", [])),
            json.dumps(feedback.get("weaknesses", [])),
            json.dumps(feedback.get("suggestions", [])),
            feedback.get("insights", ""),
            json.dumps(feedback.get("roadmap", {}).get("immediate_fixes", [])),
            json.dumps(feedback.get("roadmap", {}).get("long_term_improvements", [])),
            json.dumps(feedback.get("style_confidences", {}))
        ))

        conn.commit()
        return artwork_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_report_path(artwork_id, pdf_path):
    """Saves or updates the generated PDF report path in the reports table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM reports WHERE artwork_id = ?", (artwork_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE reports SET pdf_path = ? WHERE artwork_id = ?", (pdf_path, artwork_id))
    else:
        cursor.execute("INSERT INTO reports (artwork_id, pdf_path) VALUES (?, ?)", (artwork_id, pdf_path))
    conn.commit()
    conn.close()

def get_artwork_history(user_id=1):
    """Retrieves all previously analyzed artworks with summary statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.title, a.image_path, a.created_at,
               an.composition_score, an.color_score, an.contrast_score, an.aesthetic_score,
               an.style, an.verdict, r.pdf_path
        FROM artworks a
        JOIN analysis an ON a.id = an.artwork_id
        LEFT JOIN reports r ON a.id = r.artwork_id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_artwork_detail(artwork_id):
    """Retrieves the full artwork, metrics, and AI critique detail for a specific artwork ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
    artwork_row = cursor.fetchone()
    if not artwork_row:
        conn.close()
        return None
        
    cursor.execute("SELECT * FROM analysis WHERE artwork_id = ?", (artwork_id,))
    analysis_row = cursor.fetchone()
    
    cursor.execute("SELECT * FROM ai_feedback WHERE artwork_id = ?", (artwork_id,))
    feedback_row = cursor.fetchone()
    
    cursor.execute("SELECT pdf_path FROM reports WHERE artwork_id = ?", (artwork_id,))
    report_row = cursor.fetchone()

    conn.close()

    result = {
        **dict(artwork_row),
        "metrics": dict(analysis_row) if analysis_row else {},
        "pdf_path": report_row["pdf_path"] if report_row else None
    }

    if feedback_row:
        feedback_dict = dict(feedback_row)
        result["feedback"] = {
            "strengths": json.loads(feedback_dict.get("strengths", "[]")),
            "weaknesses": json.loads(feedback_dict.get("weaknesses", "[]")),
            "suggestions": json.loads(feedback_dict.get("suggestions", "[]")),
            "insights": feedback_dict.get("insights", ""),
            "roadmap_immediate": json.loads(feedback_dict.get("roadmap_immediate", "[]")),
            "roadmap_longterm": json.loads(feedback_dict.get("roadmap_longterm", "[]")),
            "style_percentages": json.loads(feedback_dict.get("style_percentages", "{}")),
        }
    else:
        result["feedback"] = {}

    return result

def get_average_scores(user_id=1):
    """Calculates average scores across all analyses for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            AVG(an.composition_score) as avg_composition,
            AVG(an.color_score) as avg_color,
            AVG(an.contrast_score) as avg_contrast,
            AVG(an.aesthetic_score) as avg_aesthetic,
            COUNT(a.id) as total_uploads
        FROM artworks a
        JOIN analysis an ON a.id = an.artwork_id
        WHERE a.user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row["total_uploads"] > 0:
        return {
            "avg_composition": round(row["avg_composition"], 1),
            "avg_color": round(row["avg_color"], 1),
            "avg_contrast": round(row["avg_contrast"], 1),
            "avg_aesthetic": round(row["avg_aesthetic"], 1),
            "total_uploads": row["total_uploads"]
        }
    return {
        "avg_composition": 0.0,
        "avg_color": 0.0,
        "avg_contrast": 0.0,
        "avg_aesthetic": 0.0,
        "total_uploads": 0
    }

def get_score_trends(user_id=1):
    """Retrieves chronological analysis history to plot trends in visual skills."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.created_at, 
               an.composition_score, 
               an.color_score, 
               an.contrast_score, 
               an.aesthetic_score
        FROM artworks a
        JOIN analysis an ON a.id = an.artwork_id
        WHERE a.user_id = ?
        ORDER BY a.created_at ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_artwork(artwork_id):
    """Deletes artwork record and its associated physical files (image & PDF)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get file paths to delete from disk
    cursor.execute("SELECT image_path FROM artworks WHERE id = ?", (artwork_id,))
    img_row = cursor.fetchone()
    cursor.execute("SELECT pdf_path FROM reports WHERE artwork_id = ?", (artwork_id,))
    pdf_row = cursor.fetchone()

    # Cascade delete in SQLite (requires foreign_keys pragma or manual delete)
    # Ensure SQLite enforces cascade delete:
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM artworks WHERE id = ?", (artwork_id,))
    conn.commit()
    conn.close()

    # Delete files from filesystem
    if img_row and os.path.exists(img_row["image_path"]):
        try:
            os.remove(img_row["image_path"])
        except Exception:
            pass
            
    if pdf_row and os.path.exists(pdf_row["pdf_path"]):
        try:
            os.remove(pdf_row["pdf_path"])
        except Exception:
            pass
