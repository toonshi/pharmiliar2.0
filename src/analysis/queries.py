from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from models import Department, Service, PriceHistory
import os

def get_session():
    """Create a database session"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          'data', 'processed', 'hospital_services.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()

def get_service_by_code(code):
    """Find a service by its code"""
    with get_session() as session:
        return session.query(Service).filter(Service.code == code).first()

def get_services_by_department(department_name):
    """Get all services in a department"""
    with get_session() as session:
        dept = session.query(Department).filter(Department.name == department_name).first()
        if dept:
            return dept.services
        return []

def get_price_comparison(service_code):
    """Compare different price tiers for a service"""
    with get_session() as session:
        service = session.query(Service).filter(Service.code == service_code).first()
        if service:
            return {
                'code': service.code,
                'description': service.description,
                'normal_rate': service.normal_rate,
                'special_rate': service.special_rate,
                'non_ea_rate': service.non_ea_rate,
                'department': service.department.name,
                'gl_account': service.gl_account or service.department.gl_account
            }
        return None

def get_service_variants(base_code):
    """Get all variants of a service (K, NK, P versions)"""
    with get_session() as session:
        base_service = session.query(Service).filter(
            Service.code == base_code,
            Service.variant_type == None
        ).first()
        
        if base_service:
            variants = session.query(Service).filter(
                Service.base_service_id == base_service.id
            ).all()
            
            return {
                'base_service': base_service,
                'variants': variants
            }
        return None

def get_department_summary():
    """Get summary of services and price ranges by department"""
    with get_session() as session:
        departments = session.query(Department).all()
        summary = []
        
        for dept in departments:
            service_count = session.query(func.count(Service.id))\
                .filter(Service.department_id == dept.id).scalar()
            
            price_stats = session.query(
                func.min(Service.normal_rate).label('min_price'),
                func.max(Service.normal_rate).label('max_price'),
                func.avg(Service.normal_rate).label('avg_price')
            ).filter(Service.department_id == dept.id).first()
            
            summary.append({
                'department': dept.name,
                'service_count': service_count,
                'min_price': price_stats.min_price,
                'max_price': price_stats.max_price,
                'avg_price': price_stats.avg_price,
                'gl_account': dept.gl_account
            })
        
        return summary

if __name__ == '__main__':
    # Example usage
    print("\n1. Looking up a specific service:")
    service = get_service_by_code("LAB001")
    if service:
        print(f"Service: {service.description}")
        print(f"Normal Rate: {service.normal_rate}")
        print(f"Department: {service.department.name}")

    print("\n2. Department Summary:")
    summary = get_department_summary()
    for dept in summary[:3]:  # Show first 3 departments
        print(f"\nDepartment: {dept['department']}")
        print(f"Number of Services: {dept['service_count']}")
        print(f"Price Range: {dept['min_price']} - {dept['max_price']}")
        print(f"Average Price: {dept['avg_price']:.2f}")

    print("\n3. Service Variants Example:")
    variants = get_service_variants("LAB001")
    if variants:
        print(f"Base Service: {variants['base_service'].description}")
        print("Variants:")
        for var in variants['variants']:
            print(f"- {var.variant_type}: {var.normal_rate}")
