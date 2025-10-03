import json
from neo4j import GraphDatabase, RoutingControl
from person import Person
from config import *

def chunks(xs, n=10):
    n = max(1, n)
    return [xs[i:i + n] for i in range(0, len(xs), n)]

def load_person_infor():
    with open(EXTRACTED_JSON, 'r', encoding='utf-8') as file:
        people_json = json.load(file)
    people = [Person(**person) for person in people_json]
    return [p.model_dump() for p in people]

class KnowledgeGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    def test_connection(self):
        self.driver.execute_query("MATCH(n) RETURN count(n)")
    
    def refresh_graph(self):
        self.driver.execute_query("MATCH(N) DETACH DELETE N")
    @staticmethod
    def merge_skills_accomplishments(people_json, type):
        results = []
        for person in people_json:
            tmp_results = person[type].copy()
            for item in tmp_results:
                item['personId'] = person['id']
            results.extend(tmp_results)
        return results
    def initialize_graph(self, people_json):
        self.driver.execute_query(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (n:Person) REQUIRE (n.id) IS NODE KEY',
            routing_=RoutingControl.WRITE
        )

        self.driver.execute_query(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (n:Skill) REQUIRE (n.name) IS NODE KEY',
            routing_=RoutingControl.WRITE
        )

        self.driver.execute_query(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (n:Thing) REQUIRE (n.name) IS NODE KEY',
            routing_=RoutingControl.WRITE
        )

        self.driver.execute_query(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (n:Domain) REQUIRE (n.name) IS NODE KEY',
            routing_=RoutingControl.WRITE
        )

        self.driver.execute_query(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (n:WorkType) REQUIRE (n.name) IS NODE KEY',
            routing_=RoutingControl.WRITE
        )
        for chunk in chunks(people_json):
            records = self.driver.execute_query(
                """
                UNWIND $records AS rec
                MERGE(person:Person {id:rec.id})
                SET person.name = rec.name,
                    person.email = rec.email,
                    person.current_title = rec.current_title,
                    person.department = rec.department,
                    person.level = rec.level,
                    person.years_experience = rec.years_experience,
                    person.location = rec.location
                RETURN count(rec) AS records_upserted
                """,
                routing_=RoutingControl.WRITE,
                result_transformer_= lambda r: r.data(),
                records = chunk
            )
            print(records)
        
        merged_skills = self.merge_skills_accomplishments(people_json, type="skills")
        merged_accomplishments = self.merge_skills_accomplishments(people_json, type="accomplishments")
        for chunk in chunks(merged_skills):
            records = self.driver.execute_query(
                # MATCH tìm person theo personID, nếu không có thì skip
                # MERGE tìm skill theo skillName, nếu không có thì tạo mới
                # MERGE(person)-[r:KNOWS]->(skill) tạo quan hệ KNOWS giữa person và skill
                # SET r là set cho quan hệ KNOWS
                """
                UNWIND $records AS rec
                MATCH(person:Person {id:rec.personId})
                MERGE(skill:Skill {name:rec.skill.name})
                MERGE(person)-[r:KNOWS]->(skill)
                SET r.proficiency = rec.proficiency,
                    r.years_experience = rec.years_experience,
                    r.context  = rec.context,
                    r.is_primary = rec.is_primary
                RETURN count(rec) AS records_upserted
                """,
                routing_=RoutingControl.WRITE,
                result_transformer_=lambda r: r.data(),
                records = chunk
            )
            print(records)
        for chunk in chunks(merged_accomplishments):
            records = self.driver.execute_query(
                """
                UNWIND $records AS rec

                //match people
                MATCH(person:Person {id:rec.personId})

                //merge accomplishments
                MERGE(thing:Thing {name:rec.thing.name})
                MERGE(person)-[r:$(rec.type)]->(thing)
                SET r.impact_description = rec.impact_description,
                    r.year = rec.year,
                    r.role  = rec.role,
                    r.duration = rec.duration,
                    r.team_size = rec.team_size,
                    r.context  = rec.context

                //merge domain and work type
                MERGE(Domain:Domain {name:rec.thing.domain})
                MERGE(thing)-[:IN]->(Domain)
                MERGE(WorkType:WorkType {name:rec.thing.type})
                MERGE(thing)-[:OF]->(WorkType)

                RETURN count(rec) AS records_upserted
                """,
                #database_=DATABASE,
                routing_=RoutingControl.WRITE,
                result_transformer_= lambda r: r.data(),
                records = chunk
            )
            print(records)

if __name__ == "__main__":
    knowledge_graph = KnowledgeGraph()
    # knowledge_graph.test_connection()
    # knowledge_graph.refresh_graph()
    result = knowledge_graph.driver.execute_query("MATCH (n:Person) RETURN count(n) AS cnt")
    person_count = result.records[0]['cnt'] if result.records else 0
    if person_count == 0:
        people = load_person_infor()
        knowledge_graph.initialize_graph(people)
    else:
        print(f"Neo4j đã có {person_count} node Person, bỏ qua bước nạp dữ liệu.")
# sửa resume về hết tiếng việt và up lên neo4j
# test mcp server với neo4j trước
# thêm notion vào tools, sửa prompt của cả agent và orchestrator