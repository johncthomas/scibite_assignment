
from requests import Session
from datetime import datetime
from typing import Optional
from urllib.parse import quote

DBPEDIA = 'https://dbpedia.org/sparql'

def get_session() -> Session:
    """Create session with defaults."""
    sess = Session()
    sess.headers.update({"Accept": "application/sparql-results+json"})
    return sess


def run_query_content(query:str, sess:Session=None) -> dict:
    """Get parsed content of query."""
    if sess is None:
        sess = get_session()

    result = sess.get(
        DBPEDIA,
        params={'query':query},
        timeout=(10, 60), # (connect, read)
    )
    result.raise_for_status()
    sess.close()
    return result.json()


def get_dob(name:str) -> Optional[datetime]:
    """Returns the date of birth of the named person from dbpedia."""

    q = """
        SELECT ?dob
        FROM <http://dbpedia.org>
        WHERE {{
        dbr:{name} dbp:birthDate ?dob .
        }} LIMIT 1
    """.format(name=name)

    content = run_query_content(q)
    bindings = content['results']['bindings']
    if len(bindings) == 0:
        return None
    datestr = bindings[0]['dob']['value']
    date = datetime.strptime(datestr, "%Y-%m-%d")
    return date


def get_person_age(name:str) -> int|None:
    """Returns the age of the named person, in years."""
    result = get_dob(name)
    if result is None:
        return None
    now = datetime.now()
    age = now.year - result.year
    if (now.month < result.month) or (now.month == result.month and now.day < result.day):
        age -= 1
    return age


def get_birth_name(name:str) -> Optional[str]:
    """Returns the person's birth name from dbpedia."""
    q = """
        SELECT ?name
        FROM <http://dbpedia.org>
        WHERE {{
        dbr:{name} ?p ?name .
        FILTER (?p IN (dbp:birthname, dbp:birthName) )
        }} LIMIT 1
    """.format(name=quote(name))

    content = run_query_content(q)
    bindings = content['results']['bindings']
    if len(bindings) == 0:
        return None
    birthname = bindings[0]['name']['value']
    return birthname


def do_sparql_query(user_q:str):
    """Parse question, query dbpedia and return result."""
    user_q = user_q.replace('?', '').strip()
    questions_funcs = {
        "How old is ":get_person_age,
        "What is the birth name of ":get_birth_name,
    }
    for prefix, func in questions_funcs.items():
        if user_q.startswith(prefix):
            name = (
                user_q
                    .removeprefix(prefix)
                    .strip()
                    .replace(' ', '_')
            )
            result = func(name)
            if result is None:
                print(f"Query returned no results for {name}")
            return result

    # if the question prefix is not recognised.
    options = "\n - ".join(questions_funcs)
    print(
        f"Invalid query: {user_q}. "
        f"Valid questions start with\n - {options}"
    )
    return None


def test_do_sparql_query():
    # NOTE: the age tests will fail on the person's next birthday.
    assert do_sparql_query("How old is Donald Knuth") == 88
    assert do_sparql_query("How old is Radia Perlman") == 74 # changed from 71
    assert do_sparql_query("What is the birth name of Donald Knuth") == "Donald Ervin Knuth"
    print('tests passed')


def test_do_sparql_query_additional():
    assert do_sparql_query("How old is person does not exist") is None
    assert do_sparql_query("What is the birth name of not a real person") is None
    # bit confused by this because https://dbpedia.org/page/Martin_Luther_King_Jr. is valid
    #do_sparql_query("How old is Martin Luther King Jr.")
    assert do_sparql_query("not a real question") is None


if __name__ == '__main__':
    test_do_sparql_query()
    #test_do_sparql_query_additional()