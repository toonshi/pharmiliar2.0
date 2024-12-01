import pandas as pd
from sqlalchemy.orm import sessionmaker
from models import Department, Service, init_db
import os

def clean_price(price_str):
    """Convert price string to float, handling commas and invalid values"""
    if pd.isna(price_str) or price_str == '':
        return 0.0
    try:
        return float(str(price_str).replace(',', ''))
    except (ValueError, TypeError):
        return 0.0

def extract_variant_type(code):
    """Extract variant type from service code"""
    if code.endswith('-K'):
        return 'K'
    elif code.endswith('-NK'):
        return 'NK'
    elif code.endswith('-P'):
        return 'P'
    return None

def migrate_data(excel_path, db_path):
    """Migrate data from Excel to new database structure"""
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Initialize database
    engine = init_db(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # First pass: Create departments
        current_dept = None
        departments = {}
        
        for _, row in df.iterrows():
            # If row has no service code but has a name, it's a department header
            if pd.isna(row[1]) and pd.notna(row[0]) and isinstance(row[0], str):
                dept_name = row[0].strip()
                if dept_name not in departments:
                    dept = Department(
                        name=dept_name,
                        gl_account=row[6] if pd.notna(row[6]) else None
                    )
                    session.add(dept)
                    departments[dept_name] = dept
                current_dept = departments[dept_name]
        
        session.commit()
        
        # Second pass: Create services
        service_map = {}  # To track base services for variants
        current_dept = None
        
        for _, row in df.iterrows():
            if pd.isna(row[1]):  # Department header row
                if pd.notna(row[0]) and isinstance(row[0], str):
                    current_dept = departments.get(row[0].strip())
                continue
                
            if pd.notna(row[1]) and current_dept:  # Service row
                code = str(row[1]).strip()
                variant_type = extract_variant_type(code)
                base_code = code[:-2] if variant_type else code
                
                service = Service(
                    code=code,
                    description=str(row[2]).strip() if pd.notna(row[2]) else '',
                    normal_rate=clean_price(row[3]),
                    special_rate=clean_price(row[4]),
                    non_ea_rate=clean_price(row[5]),
                    department=current_dept,
                    gl_account=str(row[6]) if pd.notna(row[6]) else None,
                    variant_type=variant_type
                )
                
                # Link variants to their base service
                if variant_type and base_code in service_map:
                    service.base_service_id = service_map[base_code].id
                
                session.add(service)
                if not variant_type:
                    service_map[code] = service
        
        session.commit()
        print(f"Migration completed successfully. Database created at {db_path}")
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(project_root, 'data', 'raw', 'extracted_data.xlsx')
    db_path = os.path.join(project_root, 'data', 'processed', 'hospital_services.db')
    
    migrate_data(excel_path, db_path)
