from .models import HealthCheck, Project, Resource, ResourceType

PROJECTS = [
    Project(id="rdsocial", name="RD Social", description="Synthetic target application",
            repository_paths=["/workspace/projects/rdsocial"], services=["rdsocial-api"],
            databases=["rdsocial"], ports=[8101], domains=["api.rdsocialapp.test"],
            health_checks=[HealthCheck()], protected=False),
    Project(id="engageflow", name="EngageFlow", description="Synthetic protected application",
            repository_paths=["/workspace/projects/engageflow"], services=["engageflow-api"],
            databases=["engageflow"], ports=[8201], domains=["api.engageflow.test"],
            health_checks=[HealthCheck()], protected=True),
]


def resources_for(project: Project) -> list[Resource]:
    values = [
        *[(ResourceType.REPOSITORY, value) for value in project.repository_paths],
        *[(ResourceType.SERVICE, value) for value in project.services],
        *[(ResourceType.DATABASE, value) for value in project.databases],
        *[(ResourceType.PORT, str(value)) for value in project.ports],
        *[(ResourceType.DOMAIN, value) for value in project.domains],
    ]
    return [Resource(type=kind, identifier=value, project_id=project.id,
                     protected=project.protected) for kind, value in values]


def all_resources() -> list[Resource]:
    return [resource for project in PROJECTS for resource in resources_for(project)]

