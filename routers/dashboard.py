"""
Dashboard API Router
Endpoints for Stetson University dashboard analytics
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/analytics")
async def get_analytics():
    """Get dashboard analytics data"""
    try:
        # Simulate analytics data (in production, this would come from a database)
        analytics = {
            "high_priority_alerts": {
                "escalated_tickets": 12,
                "sla_warnings": 5,
                "system_alerts": 2
            },
            "recent_tickets": [
                {
                    "id": "#789123",
                    "student": "Jane Doe",
                    "topic": "Financial Aid Inquiry",
                    "status": "Urgent",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "id": "#789124",
                    "student": "John Smith", 
                    "topic": "Housing Application Error",
                    "status": "High",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    "id": "#789125",
                    "student": "Emily White",
                    "topic": "Course Registration Issue", 
                    "status": "High",
                    "timestamp": (datetime.now() - timedelta(hours=4)).isoformat()
                }
            ],
            "inquiry_topics": [
                {"topic": "Financial Aid", "count": 120, "color": "#42A5F5"},
                {"topic": "Housing", "count": 95, "color": "#66BB6A"},
                {"topic": "Registration", "count": 80, "color": "#FFEE58"},
                {"topic": "IT Support", "count": 65, "color": "#AB47BC"},
                {"topic": "Admissions", "count": 40, "color": "#EC407A"}
            ],
            "communication_channels": {
                "last_24h": [
                    {"time": "8am", "calls": 15, "texts": 30},
                    {"time": "10am", "calls": 25, "texts": 45},
                    {"time": "12pm", "calls": 40, "texts": 60},
                    {"time": "2pm", "calls": 35, "texts": 55},
                    {"time": "4pm", "calls": 50, "texts": 70},
                    {"time": "6pm", "calls": 30, "texts": 50},
                    {"time": "8pm", "calls": 20, "texts": 40}
                ]
            },
            "frequent_questions": [
                {"question": "Do you offer on campus housing?", "count": 15, "topic": "Housing"},
                {"question": "Can I make an appointment with financial aid?", "count": 8, "topic": "Financial Aid"},
                {"question": "How do I register for classes?", "count": 12, "topic": "Registration"},
                {"question": "What are the admission requirements?", "count": 6, "topic": "Admissions"}
            ]
        }
        
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/alerts")
async def get_alerts():
    """Get high priority alerts"""
    try:
        alerts = {
            "escalated_tickets": [
                {
                    "id": "#789123",
                    "student": "Jane Doe",
                    "topic": "Financial Aid Inquiry",
                    "priority": "Urgent",
                    "escalated_at": datetime.now().isoformat(),
                    "assigned_to": "Admissions Team"
                },
                {
                    "id": "#789124", 
                    "student": "John Smith",
                    "topic": "Housing Application Error",
                    "priority": "High",
                    "escalated_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "assigned_to": "Housing Office"
                }
            ],
            "sla_warnings": [
                {
                    "id": "#789125",
                    "student": "Emily White", 
                    "topic": "Course Registration Issue",
                    "priority": "High",
                    "sla_deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "assigned_to": "Registrar Office"
                }
            ],
            "system_alerts": [
                {
                    "type": "High CPU Usage",
                    "message": "Server CPU usage above 80%",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "Warning"
                }
            ]
        }
        
        return {
            "status": "success",
            "data": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/communications")
async def get_communications():
    """Get communication channel analytics"""
    try:
        # Generate realistic communication data
        communications = {
            "channels": {
                "phone_calls": {
                    "successful": random.randint(80, 120),
                    "failed": random.randint(5, 15),
                    "avg_duration": "4.2 minutes"
                },
                "text_messages": {
                    "sent": random.randint(200, 300),
                    "delivered": random.randint(190, 290),
                    "response_rate": "85%"
                },
                "email": {
                    "sent": random.randint(150, 200),
                    "opened": random.randint(120, 180),
                    "response_rate": "70%"
                }
            },
            "trends": {
                "peak_hours": ["10am-12pm", "2pm-4pm"],
                "busiest_day": "Tuesday",
                "response_time_avg": "2.3 minutes"
            }
        }
        
        return {
            "status": "success", 
            "data": communications,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get communications: {str(e)}")

@router.get("/faq")
async def get_faq():
    """Get frequent questions data"""
    try:
        faq_data = {
            "top_questions": [
                {
                    "question": "Do you offer on campus housing?",
                    "count": 15,
                    "topic": "Housing",
                    "last_asked": (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    "question": "Can I make an appointment with financial aid?",
                    "count": 8,
                    "topic": "Financial Aid", 
                    "last_asked": (datetime.now() - timedelta(hours=4)).isoformat()
                },
                {
                    "question": "How do I register for classes?",
                    "count": 12,
                    "topic": "Registration",
                    "last_asked": (datetime.now() - timedelta(hours=1)).isoformat()
                },
                {
                    "question": "What are the admission requirements?",
                    "count": 6,
                    "topic": "Admissions",
                    "last_asked": (datetime.now() - timedelta(hours=6)).isoformat()
                }
            ],
            "topics": [
                {"name": "Housing", "count": 45, "percentage": 35},
                {"name": "Financial Aid", "count": 38, "percentage": 30},
                {"name": "Registration", "count": 25, "percentage": 20},
                {"name": "Admissions", "count": 15, "percentage": 12},
                {"name": "IT Support", "count": 5, "percentage": 3}
            ]
        }
        
        return {
            "status": "success",
            "data": faq_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FAQ data: {str(e)}")

@router.get("/summary")
async def get_dashboard_summary():
    """Get complete dashboard summary"""
    try:
        summary = {
            "total_inquiries": 128,
            "resolved_today": 45,
            "pending": 12,
            "escalated": 3,
            "avg_response_time": "2.3 minutes",
            "satisfaction_score": 4.7,
            "active_agents": 8,
            "peak_hour": "2pm-4pm"
        }
        
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
