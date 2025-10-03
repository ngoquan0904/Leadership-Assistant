from enum import Enum
from pydantic import BaseModel, Field
class Domain(str, Enum):
    """Domain categories for technical/business areas"""
    AI = "AI"                           # Machine learning, neural networks, AI systems
    DATA_ENGINEERING = "DATA_ENGINEERING"  # Data pipelines, ETL, data platforms
    ANALYTICS = "ANALYTICS"             # BI, reporting, dashboards, data analysis
    DATABASE = "DATABASE"               # Database systems, storage, optimization
    WEB = "WEB"                         # Frontend, web applications, web platforms
    MOBILE = "MOBILE"                   # iOS, Android, mobile applications
    CLOUD = "CLOUD"                     # AWS, Azure, GCP, cloud architecture
    DEVOPS = "DEVOPS"                   # CI/CD, deployment, automation
    SECURITY = "SECURITY"               # Cybersecurity, auth, compliance
    MICROSERVICES = "MICROSERVICES"     # Service architecture, APIs, distributed systems
    PLATFORM = "PLATFORM"               # Internal tools, developer platforms

class WorkType(str, Enum):
    """WorkType categories for type of work performed"""
    SYSTEM = "SYSTEM"           # Technical systems/platforms
    RESEARCH = "RESEARCH"       # Papers, studies, R&D
    PRODUCT = "PRODUCT"         # Customer-facing features/apps
    TEAM = "TEAM"               # Groups of people
    PROJECT = "PROJECT"         # Time-bounded initiatives
    PROCESS = "PROCESS"         # Workflows, procedures
    AWARD = "AWARD"             # Recognition, honors
    CODE = "CODE"               # Open source, libraries

class Thing(BaseModel):
    """Node representing what was accomplished"""
    name: str = Field(..., description="Unique identifier name for the the thing. "
                                       "This should be unique across all accomplished things and somewhat descriptive."
                                       "Concat the person id to this name to ensure uniqueness across multiple people.")
    type: WorkType = Field(..., description="Type of thing")
    domain: Domain = Field(..., description="Domain/category of thing")
class SkillName(str, Enum):
    """Standardized skill names"""
    # AI/ML Skills
    MACHINE_LEARNING = "Machine Learning"
    DEEP_LEARNING = "Deep Learning"
    NATURAL_LANGUAGE_PROCESSING = "Natural Language Processing"
    COMPUTER_VISION = "Computer Vision"
    DATA_SCIENCE = "Data Science"
    STATISTICS = "Statistics"

    # AI/ML & Analytics Frameworks & Libraries
    TENSORFLOW = "TensorFlow"
    PYTORCH = "PyTorch"
    KERAS = "Keras"
    SCIKIT_LEARN = "Scikit-learn"
    PANDAS = "Pandas"
    NUMPY = "NumPy"
    MATPLOTLIB = "Matplotlib"

    # Programming Languages
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    JAVA = "Java"
    CPP = "C++"
    C = "C"
    CSHARP = "C#"
    GO = "Go"
    RUST = "Rust"
    RUBY = "Ruby"
    SWIFT = "Swift"
    KOTLIN = "Kotlin"
    R = "R Programming Language"
    SQL = "SQL"
    SCALA = "Scala"

    # Frontend Frameworks & Libraries
    REACT = "React"
    ANGULAR = "Angular"
    VUE = "Vue.js"
    SVELTE = "Svelte"
    NEXT_JS = "Next.js"
    NUXT = "Nuxt.js"

    # Backend Frameworks
    NODE_JS = "Node.js"
    EXPRESS = "Express.js"
    DJANGO = "Django"
    FLASK = "Flask"
    SPRING = "Spring"
    RUBY_ON_RAILS = "Ruby on Rails"
    LARAVEL = "Laravel"
    ASP_NET = "ASP.NET"
    NEST_JS = "Nest.js"

    # Data/Infrastructure Skills
    DATA_ENGINEERING = "Data Engineering"
    CLOUD_ARCHITECTURE = "Cloud Architecture"
    AWS = "AWS"
    AZURE = "Azure"
    GCP = "Google Cloud Platform"
    DOCKER = "Docker"
    KUBERNETES = "Kubernetes"

    # Product/Business Skills
    PRODUCT_STRATEGY = "Product Strategy"
    PRODUCT_MANAGEMENT = "Product Management"
    DATA_ANALYSIS = "Data Analysis"
    BUSINESS_INTELLIGENCE = "Business Intelligence"

    # Soft Skills
    LEADERSHIP = "Leadership"
    TEAM_MANAGEMENT = "Team Management"
    COMMUNICATION = "Communication"
    PROJECT_MANAGEMENT = "Project Management"

    # Other Skills
    ADOBE_PHOTOSHOP = "Adobe Photoshop"
    SOCIAL_MEDIA_MARKETING = "Social Media Marketing"
    ACCOUNTING = "Accounting"
    LEGAL_RESEARCH = "Legal Research"