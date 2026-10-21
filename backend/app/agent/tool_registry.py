import inspect
from typing import Dict, Any, Callable, List
from ..tools import college_tools
from ..tools import web_tools


# Registered Tool Functions
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "search_faq": college_tools.search_faq,
    "get_department": college_tools.get_department,
    "get_room": college_tools.get_room,
    "get_faculty": college_tools.get_faculty,
    "get_college_hours": college_tools.get_college_hours,
    "get_upcoming_events": college_tools.get_upcoming_events,
    "get_announcements": college_tools.get_announcements,
    "search_college_documents": college_tools.search_college_documents,
    "search_internet": web_tools.search_internet,
}


# Tool Definitions for Ollama Function Calling
OLLAMA_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "Search college FAQs for questions on fees, admissions, library card, certificates, hostel, or general queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords or search phrase (e.g., 'fees', 'hostel', 'bonafide')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_department",
            "description": "Get location, floor, HOD name, contact email, and details for a college department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Department name or code (e.g., 'Computer Science', 'CSE', 'Mechanical', 'ECE', 'Civil', 'MBA')."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_room",
            "description": "Find the building, floor, and purpose for an auditorium, lab, principal office, or room.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_name": {
                        "type": "string",
                        "description": "Name or number of the room (e.g., 'Auditorium', 'Lab-204', 'Principal Office', '102', 'Library')."
                    }
                },
                "required": ["room_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_faculty",
            "description": "Look up faculty designation, department, cabin location, email, and consulting hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Faculty member's name or department to search (e.g., 'Arvind Sharma', 'Sneha Patil', 'Rajeshwari')."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_college_hours",
            "description": "Retrieve daily opening and closing hours for campus gates, central library, admin office, and food court.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "List scheduled upcoming college events, symposiums, hackathons, and placement drives.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_announcements",
            "description": "Check current college circulars, exam notices, and urgent student updates.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_college_documents",
            "description": "Search college documents (prospectus, eligibility, scholarship rules, hostel rules, handbook) with source citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific query regarding prospectus, admissions, scholarships, fees, or regulations."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "Search the live Internet when external or recent world information outside the college is requested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "External query string to search on the web."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Executes a registered tool with validation and error handling."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return f"Error: Tool '{tool_name}' is not registered."

    try:
        # Check if async
        if inspect.iscoroutinefunction(func):
            result = await func(**arguments)
        else:
            result = func(**arguments)
        return result
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"
