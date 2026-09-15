-- =============================================================
-- LearnQwik — seed data
--
-- GENERATED FILE. Do not edit by hand.
-- Regenerate with:  node tools/generate-seed.js
--
-- Source of truth: frontend/js/data.js
-- Run this AFTER database/schema.sql in the Supabase SQL editor.
-- Idempotent: re-running updates rows rather than duplicating them.
-- =============================================================

begin;

-- ---------- SUBJECTS ----------
insert into subjects (id, name, tagline, color, position) values
  ('java', 'Java', 'Object-oriented programming on the JVM', '#ff2e6e', 0)
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;
insert into subjects (id, name, tagline, color, position) values
  ('python', 'Python', 'Readable, dynamic, and everywhere in data & AI', '#00fff5', 1)
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;
insert into subjects (id, name, tagline, color, position) values
  ('dbms', 'DBMS', 'Databases, SQL, and how data is stored and queried', '#ffb02e', 2)
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;
insert into subjects (id, name, tagline, color, position) values
  ('dsa', 'Data Structures', 'Arrays, trees, graphs, and algorithmic thinking', '#a259ff', 3)
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;
insert into subjects (id, name, tagline, color, position) values
  ('c', 'C Programming', 'Close to the metal: memory, pointers, and control', '#39ff88', 4)
on conflict (id) do update set
  name = excluded.name, tagline = excluded.tagline,
  color = excluded.color, position = excluded.position;

-- ---------- TOPICS (content preserved verbatim from data.js) ----------
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-fundamentals', 'java', 'Java Fundamentals', 'Variables, primitive types, operators, and the anatomy of a Java program.',
   '{"intro":"Every Java program starts life as a class. Before you can build anything larger, you need a solid grip on how Java stores data, the difference between primitives and objects, and how the compiler and JVM turn your .java file into running bytecode.","concepts":["Eight primitive types (int, double, boolean, char, byte, short, long, float) are stored by value, not by reference.","Every .java file needs a public class matching the filename, and a main method as the entry point.","Type casting is automatic when widening (int → long) but must be explicit when narrowing (long → int)."],"practical":"The JVM compiles your source into platform-independent bytecode (.class files), which the runtime then interprets or JIT-compiles per machine — this is the ''write once, run anywhere'' promise.","examples":[{"lang":"java","code":"public class Main {\n    public static void main(String[] args) {\n        int score = 92;\n        double average = score / 2.0;\n        System.out.println(\"Average: \" + average);\n    }\n}"}],"mistakes":["Dividing two ints (score / 2) truncates the result instead of producing a decimal — cast one operand to double.","Forgetting that String comparison needs .equals(), since == compares object references, not content."],"important":["The main method signature must be exactly: public static void main(String[] args).","Java is statically typed — every variable''s type is fixed at compile time."]}'::jsonb,
   0, 25, '{}')
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-oop', 'java', 'Object-Oriented Programming', 'Classes, objects, encapsulation, and the four pillars of OOP in Java.',
   '{"intro":"Java was built around objects from day one. Understanding how classes bundle state and behavior together — and how encapsulation controls access to that state — is the foundation for everything else in the language.","concepts":["A class is a blueprint; an object is an instance of that blueprint created with ''new''.","Encapsulation means keeping fields private and exposing controlled access via getters/setters.","Constructors initialize object state and can be overloaded for different creation patterns."],"practical":"In real codebases, encapsulation prevents invalid state — a BankAccount class won''t let external code set balance directly to a negative number if the field is private and only modified through a validated withdraw() method.","examples":[{"lang":"java","code":"public class BankAccount {\n    private double balance;\n\n    public BankAccount(double initial) {\n        this.balance = initial;\n    }\n\n    public void withdraw(double amount) {\n        if (amount > balance) throw new IllegalArgumentException(\"Insufficient funds\");\n        balance -= amount;\n    }\n}"}],"mistakes":["Making all fields public ''for convenience'', which defeats encapsulation entirely.","Forgetting that ''this'' is needed when a constructor parameter shadows a field name."],"important":["The four pillars of OOP: encapsulation, inheritance, polymorphism, abstraction.","Constructors never have a return type, not even void."]}'::jsonb,
   1, 30, ARRAY['java-fundamentals']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-inheritance', 'java', 'Inheritance and Polymorphism', 'Extending classes, overriding methods, and dynamic dispatch.',
   '{"intro":"Inheritance lets a subclass reuse and extend a superclass''s behavior. Polymorphism then lets you treat different subclasses uniformly through a shared supertype reference — the mechanism behind most flexible Java designs.","concepts":["The ''extends'' keyword creates an is-a relationship between subclass and superclass.","@Override lets a subclass replace a superclass method''s behavior; the JVM picks the version at runtime.","''super'' calls the parent class''s constructor or method from within a subclass."],"practical":"A List<Shape> can hold Circle and Square objects; calling shape.area() runs each object''s own overridden implementation without the caller needing to know the concrete type — this is dynamic dispatch.","examples":[{"lang":"java","code":"class Shape {\n    double area() { return 0; }\n}\nclass Circle extends Shape {\n    double radius;\n    Circle(double r) { radius = r; }\n    @Override\n    double area() { return Math.PI * radius * radius; }\n}"}],"mistakes":["Confusing method overriding (same signature, runtime polymorphism) with overloading (different signature, compile-time).","Forgetting to call super(...) when the parent class has no no-arg constructor."],"important":["Java supports single inheritance for classes but multiple inheritance via interfaces.","A private method cannot be overridden — subclasses can only hide it."]}'::jsonb,
   2, 35, ARRAY['java-oop']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-exceptions', 'java', 'Exception Handling', 'try/catch, checked vs unchecked exceptions, and custom exceptions.',
   '{"intro":"Exceptions let Java code fail predictably instead of crashing silently. Knowing when to catch, when to propagate, and when to define your own exception type is core to writing production-grade Java.","concepts":["Checked exceptions (like IOException) must be declared or caught; unchecked (RuntimeException) don''t require it.","A try block can have multiple catch clauses, ordered from most specific to most general.","finally always runs, whether or not an exception occurred — ideal for closing resources."],"practical":"Custom exceptions (extending Exception or RuntimeException) let you model domain-specific failures, like InsufficientFundsException, instead of throwing generic RuntimeExceptions everywhere.","examples":[{"lang":"java","code":"try {\n    int[] arr = new int[3];\n    System.out.println(arr[5]);\n} catch (ArrayIndexOutOfBoundsException e) {\n    System.out.println(\"Bad index: \" + e.getMessage());\n} finally {\n    System.out.println(\"Cleanup runs regardless\");\n}"}],"mistakes":["Catching Exception broadly and swallowing it silently, hiding real bugs.","Forgetting that a return inside try still executes finally before returning."],"important":["try-with-resources automatically closes any AutoCloseable resource.","Multiple catch blocks are checked top-to-bottom; put subclasses before superclasses."]}'::jsonb,
   3, 40, ARRAY['java-inheritance']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-collections', 'java', 'Collections Framework', 'List, Set, Map, and choosing the right data structure.',
   '{"intro":"The Collections Framework is Java''s standard toolkit for storing groups of objects. Picking the right interface — List, Set, or Map — and the right implementation shapes both correctness and performance.","concepts":["List (ArrayList, LinkedList) preserves order and allows duplicates.","Set (HashSet, TreeSet) enforces uniqueness; TreeSet keeps elements sorted.","Map (HashMap, TreeMap) stores key-value pairs with O(1) average lookup for HashMap."],"practical":"Use ArrayList when you need fast random access and rarely insert in the middle; use LinkedList when you frequently insert/remove from the ends; use HashMap for O(1) lookups keyed by an identifier.","examples":[{"lang":"java","code":"Map<String, Integer> scores = new HashMap<>();\nscores.put(\"Aisha\", 92);\nscores.put(\"Rahul\", 87);\nfor (Map.Entry<String, Integer> entry : scores.entrySet()) {\n    System.out.println(entry.getKey() + \": \" + entry.getValue());\n}"}],"mistakes":["Using ArrayList when frequent insertions/removals in the middle are needed — LinkedList fits better there.","Forgetting to override equals() and hashCode() together for custom objects used as HashMap keys."],"important":["ArrayList get() is O(1); LinkedList get() is O(n).","HashMap does not guarantee iteration order; use LinkedHashMap if you need insertion order."]}'::jsonb,
   4, 45, ARRAY['java-exceptions']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('java-multithreading', 'java', 'Multithreading', 'Threads, synchronization, and avoiding race conditions.',
   '{"intro":"Java has had built-in threading support since its first release. Understanding how threads share memory — and where that sharing goes wrong — is essential before writing any concurrent code.","concepts":["A Thread can be created by extending Thread or implementing Runnable (preferred, since Java allows only single inheritance).","A race condition happens when two threads read-modify-write shared state without coordination.","The synchronized keyword ensures only one thread executes a block/method on a given lock at a time."],"practical":"A counter incremented by multiple threads without synchronization can lose updates — two threads can both read the same value before either writes back, silently dropping an increment.","examples":[{"lang":"java","code":"class Counter {\n    private int count = 0;\n    public synchronized void increment() {\n        count++;\n    }\n    public int getCount() { return count; }\n}"}],"mistakes":["Assuming ++ is atomic — it''s actually read, increment, write, which is unsafe across threads.","Synchronizing on different lock objects for the same shared data, which provides no real protection."],"important":["Prefer java.util.concurrent utilities (ExecutorService, AtomicInteger) over raw Thread management in real code.","Deadlock occurs when two threads each hold a lock the other needs."]}'::jsonb,
   5, 50, ARRAY['java-collections']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-fundamentals', 'python', 'Python Fundamentals', 'Variables, dynamic typing, and Python''s core syntax.',
   '{"intro":"Python trades explicit type declarations for readability and speed of writing. Understanding dynamic typing, indentation-based blocks, and Python''s core data types is the entry point to everything else in the language.","concepts":["Variables are dynamically typed — the same name can be rebound to different types at runtime.","Indentation (not braces) defines code blocks, so consistent spacing is syntactically required.","Core built-in types include int, float, str, bool, list, tuple, dict, and set."],"practical":"Because Python is dynamically typed, a function written once can often operate on many different types (duck typing) as long as they support the operations used inside it.","examples":[{"lang":"python","code":"def average(numbers):\n    return sum(numbers) / len(numbers)\n\nscores = [92, 87, 78, 95]\nprint(f\"Average: {average(scores):.1f}\")"}],"mistakes":["Mixing tabs and spaces for indentation, which raises an IndentationError.","Assuming lists are copied on assignment — b = a just creates a second reference to the same list."],"important":["Python uses zero-based indexing, same as Java and C.","f-strings (f\"...\") are the modern, preferred way to format strings."]}'::jsonb,
   0, 25, '{}')
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-functions', 'python', 'Functions and Modules', 'Defining functions, default arguments, and organizing code into modules.',
   '{"intro":"Functions are first-class citizens in Python — they can be passed around, stored in variables, and returned from other functions. Modules then let you split code across files and reuse it anywhere.","concepts":["def defines a function; parameters can have default values, evaluated once at definition time.","*args and **kwargs let a function accept a variable number of positional/keyword arguments.","import brings in code from another module; from module import name brings in specific names."],"practical":"A mutable default argument (like def f(x=[])) is a classic Python trap — the same list object is reused across every call unless you guard against it.","examples":[{"lang":"python","code":"def greet(name, greeting=\"Hello\"):\n    return f\"{greeting}, {name}!\"\n\nprint(greet(\"Priya\"))\nprint(greet(\"Sam\", greeting=\"Hey\"))"}],"mistakes":["Using a mutable object (list/dict) as a default argument, which persists across calls unexpectedly.","Shadowing a built-in module name (e.g. naming a file random.py) which breaks imports."],"important":["Functions without an explicit return statement return None.","__name__ == \"__main__\" guards code that should only run when the file is executed directly."]}'::jsonb,
   1, 30, ARRAY['python-fundamentals']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-oop', 'python', 'Object-Oriented Programming', 'Classes, self, inheritance, and dunder methods in Python.',
   '{"intro":"Python''s OOP model is flexible: classes are defined with ''class'', instance methods always take ''self'' explicitly, and special ''dunder'' methods let your objects integrate with built-in syntax like +, len(), and print().","concepts":["self refers to the instance and must be the first parameter of every instance method.","__init__ is the constructor, called automatically when an object is created.","Dunder methods like __str__, __eq__, and __len__ customize how built-ins interact with your class."],"practical":"Defining __str__ on a class controls what print(obj) displays, turning a generic memory-address dump into a readable representation.","examples":[{"lang":"python","code":"class Book:\n    def __init__(self, title, pages):\n        self.title = title\n        self.pages = pages\n\n    def __str__(self):\n        return f\"{self.title} ({self.pages}p)\""}],"mistakes":["Forgetting ''self'' as the first parameter in an instance method, causing a TypeError on call.","Confusing class attributes (shared across instances) with instance attributes (set in __init__)."],"important":["Python supports multiple inheritance directly: class C(A, B).","super().__init__() calls the parent class''s constructor from a subclass."]}'::jsonb,
   2, 35, ARRAY['python-functions']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-files', 'python', 'File Handling', 'Reading, writing, and safely managing files with context managers.',
   '{"intro":"File I/O in Python is built around a simple open/read-write/close cycle, but the ''with'' statement makes it safe by guaranteeing the file closes even if an error occurs mid-operation.","concepts":["open(path, mode) supports modes like ''r'' (read), ''w'' (write, overwrites), ''a'' (append).","The ''with'' statement (context manager) automatically closes the file when the block exits.","Reading can be done line-by-line, all at once (.read()), or as a list of lines (.readlines())."],"practical":"Using ''with open(...) as f:'' instead of manual open()/close() prevents file-handle leaks, which matter a lot when a program opens many files over its lifetime.","examples":[{"lang":"python","code":"with open(\"notes.txt\", \"w\") as f:\n    f.write(\"Study exceptions tonight.\\n\")\n\nwith open(\"notes.txt\", \"r\") as f:\n    print(f.read())"}],"mistakes":["Opening a file without ''with'' and forgetting to call .close(), leaking file handles.","Using mode ''w'' when you meant ''a'', silently erasing existing file content."],"important":["Files should generally be opened with an explicit encoding, e.g. encoding=\"utf-8\".","''with'' calls __enter__/__exit__ under the hood — the same protocol you can implement on custom classes."]}'::jsonb,
   3, 40, ARRAY['python-oop']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-exceptions', 'python', 'Exception Handling', 'try/except/finally and raising custom exceptions in Python.',
   '{"intro":"Python''s exception model is similar to Java''s in spirit but looser in syntax: any object can be raised, exceptions form a class hierarchy rooted at BaseException, and ''except'' clauses can filter by type.","concepts":["try/except/else/finally: else runs only if no exception occurred; finally always runs.","''raise'' can re-throw the current exception or raise a new one, optionally chained with ''from''.","Custom exceptions subclass Exception (not BaseException, which includes SystemExit/KeyboardInterrupt)."],"practical":"Catching bare ''except:'' swallows everything including KeyboardInterrupt — always catch a specific exception type, or at minimum ''except Exception:''.","examples":[{"lang":"python","code":"class InsufficientFundsError(Exception):\n    pass\n\ndef withdraw(balance, amount):\n    if amount > balance:\n        raise InsufficientFundsError(\"Not enough balance\")\n    return balance - amount"}],"mistakes":["Using a bare ''except:'' clause, which also catches system-exiting exceptions.","Catching an exception just to immediately re-raise it with no added handling, which adds noise."],"important":["except clauses are checked top-to-bottom, same as Java — order matters.","The ''else'' clause on try lets you separate ''code that might fail'' from ''code that runs only on success''."]}'::jsonb,
   4, 45, ARRAY['python-files']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('python-numpy', 'python', 'NumPy and Data Handling', 'Vectorized arrays and the foundation of Python''s data ecosystem.',
   '{"intro":"NumPy arrays are the backbone of Python''s data science stack. Unlike Python lists, they store homogeneous data contiguously in memory, enabling vectorized operations that are dramatically faster than manual loops.","concepts":["np.array() creates an ndarray; operations like +, *, and comparisons apply element-wise automatically.","Broadcasting lets NumPy apply operations between arrays of different but compatible shapes.","Slicing a NumPy array returns a view (shares memory), not a copy, unlike Python list slicing."],"practical":"Computing the mean of a million numbers with a Python for-loop is far slower than numpy_array.mean(), because NumPy runs the loop in optimized, pre-compiled C code.","examples":[{"lang":"python","code":"import numpy as np\n\nscores = np.array([92, 87, 78, 95])\nprint(scores.mean())\nprint(scores[scores > 85])"}],"mistakes":["Assuming a NumPy slice is an independent copy — modifying it can silently modify the original array.","Mixing Python lists and NumPy arrays in performance-critical loops, losing vectorization benefits."],"important":["Use .copy() explicitly when you need an independent array from a slice.","NumPy arrays are homogeneous — all elements share the same dtype."]}'::jsonb,
   5, 50, ARRAY['python-exceptions']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-fundamentals', 'dbms', 'Database Fundamentals', 'What a DBMS is and why we use it over flat files.',
   '{"intro":"A Database Management System organizes data so it can be reliably stored, queried, and modified by many users at once, with guarantees that flat files simply can''t offer.","concepts":["A DBMS provides data independence: applications don''t need to know the physical storage layout.","ACID properties (Atomicity, Consistency, Isolation, Durability) guarantee reliable transactions.","A schema defines the logical structure of the data — tables, columns, and relationships."],"practical":"Storing student records in a flat CSV file breaks down fast: no concurrent-write safety, no referential integrity, and no efficient way to query across multiple related files — a relational DBMS solves all three.","examples":[{"lang":"sql","code":"CREATE TABLE students (\n  id INT PRIMARY KEY,\n  name VARCHAR(100),\n  gpa DECIMAL(3,2)\n);"}],"mistakes":["Treating a DBMS purely as file storage rather than using its integrity and concurrency guarantees.","Skipping schema design and letting an application dump inconsistent data shapes into tables."],"important":["ACID stands for Atomicity, Consistency, Isolation, Durability.","A DBMS separates the logical view of data from its physical storage."]}'::jsonb,
   0, 25, '{}')
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-er-model', 'dbms', 'ER Model and Relational Model', 'Entities, relationships, and translating diagrams into tables.',
   '{"intro":"The Entity-Relationship model is how database designers think before writing a single line of SQL — mapping real-world entities and their relationships onto a diagram that later becomes tables and foreign keys.","concepts":["Entities become tables; attributes become columns; a primary key uniquely identifies each row.","Relationships (one-to-one, one-to-many, many-to-many) determine how foreign keys are placed.","A many-to-many relationship requires a junction (bridge) table with two foreign keys."],"practical":"A ''Student enrolls in Course'' relationship is many-to-many, so it needs an Enrollment table holding student_id and course_id as foreign keys, rather than a foreign key directly on either side.","examples":[{"lang":"sql","code":"CREATE TABLE enrollment (\n  student_id INT REFERENCES students(id),\n  course_id INT REFERENCES courses(id),\n  PRIMARY KEY (student_id, course_id)\n);"}],"mistakes":["Trying to model a many-to-many relationship with a foreign key on just one side.","Choosing a mutable, non-unique attribute (like name) as a primary key."],"important":["A primary key must be unique and cannot be NULL.","A foreign key enforces referential integrity between two tables."]}'::jsonb,
   1, 30, ARRAY['dbms-fundamentals']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-sql', 'dbms', 'SQL', 'Querying, filtering, joining, and aggregating relational data.',
   '{"intro":"SQL is the language you use to actually talk to a relational database — SELECT to read, JOIN to combine tables, WHERE to filter, and GROUP BY to aggregate.","concepts":["SELECT ... FROM ... WHERE is the basic query shape; ORDER BY sorts results.","INNER JOIN returns only matching rows across tables; LEFT JOIN keeps all rows from the left table.","GROUP BY aggregates rows sharing a value; HAVING filters after aggregation (WHERE filters before)."],"practical":"To find each student''s average score, you GROUP BY student_id and use AVG(score) — but to then filter for students averaging above 80, you need HAVING, since WHERE can''t reference the aggregate.","examples":[{"lang":"sql","code":"SELECT student_id, AVG(score) AS avg_score\nFROM quiz_attempts\nGROUP BY student_id\nHAVING AVG(score) > 80\nORDER BY avg_score DESC;"}],"mistakes":["Using WHERE instead of HAVING to filter on an aggregate result.","Forgetting that LEFT JOIN can produce NULLs for unmatched right-table columns."],"important":["Execution order is roughly: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY.","DISTINCT removes duplicate rows from a result set."]}'::jsonb,
   2, 35, ARRAY['dbms-er-model']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-normalization', 'dbms', 'Normalization', '1NF, 2NF, 3NF, and eliminating data redundancy.',
   '{"intro":"Normalization is the process of structuring tables to minimize redundancy and avoid update anomalies — where the same fact stored in multiple places can go out of sync.","concepts":["1NF: every column holds atomic (indivisible) values, no repeating groups.","2NF: 1NF plus every non-key column depends on the whole primary key, not just part of it.","3NF: 2NF plus no non-key column depends on another non-key column (no transitive dependency)."],"practical":"Storing a student''s department name directly in an enrollment table (instead of a department_id foreign key) means updating one department''s name requires updating every enrollment row — a classic update anomaly that normalization prevents.","examples":[{"lang":"sql","code":"-- Before: redundant department_name in every row\n-- After normalizing to 3NF:\nCREATE TABLE departments (id INT PRIMARY KEY, name VARCHAR(100));\nCREATE TABLE students (id INT PRIMARY KEY, dept_id INT REFERENCES departments(id));"}],"mistakes":["Over-normalizing to the point where every query needs five joins, hurting read performance.","Confusing 2NF with 3NF — 2NF is about partial dependency, 3NF is about transitive dependency."],"important":["Higher normal forms reduce redundancy but can increase the number of joins needed.","Denormalization is sometimes intentionally applied for read-heavy performance needs."]}'::jsonb,
   3, 40, ARRAY['dbms-sql']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-transactions', 'dbms', 'Transactions and Concurrency', 'Isolation levels, locking, and concurrent access problems.',
   '{"intro":"When multiple users hit the same database at once, transactions and isolation levels determine what can go wrong — and how much the DBMS protects you from it automatically.","concepts":["A transaction groups operations so they succeed or fail together (COMMIT / ROLLBACK).","Isolation levels (Read Uncommitted → Serializable) trade off consistency guarantees against performance.","Common concurrency problems: dirty reads, non-repeatable reads, and phantom reads."],"practical":"Two users simultaneously booking the last seat on a flight is a textbook concurrency problem — without proper isolation/locking, both transactions can read ''seat available'' before either commits, resulting in a double-booking.","examples":[{"lang":"sql","code":"BEGIN TRANSACTION;\nUPDATE seats SET booked = TRUE WHERE seat_id = 12 AND booked = FALSE;\n-- check rows affected before COMMIT\nCOMMIT;"}],"mistakes":["Assuming higher isolation levels are ''free'' — Serializable can significantly reduce throughput under load.","Forgetting to check affected row count after a conditional UPDATE, missing a lost-update scenario."],"important":["Serializable is the strictest isolation level; Read Uncommitted is the loosest.","A dirty read is seeing another transaction''s uncommitted changes."]}'::jsonb,
   4, 45, ARRAY['dbms-normalization']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dbms-indexing', 'dbms', 'Indexing and Query Optimization', 'How indexes speed up lookups and how to read a query plan.',
   '{"intro":"An index is a separate data structure (usually a B-tree) that lets the database find rows without scanning the entire table — the single biggest lever for query performance.","concepts":["Without an index, a WHERE clause on a large table forces a full table scan.","A B-tree index keeps values sorted, enabling O(log n) lookups instead of O(n).","Indexes speed up reads but slow down writes, since every INSERT/UPDATE must also update the index."],"practical":"Adding an index on students.email turns a login lookup from scanning every row to a near-instant B-tree traversal — critical once a table grows past a few thousand rows.","examples":[{"lang":"sql","code":"CREATE INDEX idx_students_email ON students(email);\n\nEXPLAIN SELECT * FROM students WHERE email = ''user@example.com'';"}],"mistakes":["Indexing every column ''just in case'', which slows down writes without meaningfully helping reads.","Not checking the query plan (EXPLAIN) before assuming an index is actually being used."],"important":["A composite index''s column order matters — it''s most useful when queries filter by the leading column(s).","EXPLAIN shows whether a query uses an index scan or a full table scan."]}'::jsonb,
   5, 50, ARRAY['dbms-transactions']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-arrays', 'dsa', 'Arrays and Strings', 'Fixed-size contiguous storage and common string manipulation patterns.',
   '{"intro":"Arrays are the simplest data structure — a contiguous block of memory holding fixed-size elements — but that simplicity hides real trade-offs around insertion cost and resizing.","concepts":["Array access by index is O(1); insertion/deletion in the middle is O(n) due to shifting.","Strings are typically implemented as arrays of characters, often immutable in many languages.","Two-pointer and sliding-window techniques solve many array/string problems in O(n) instead of O(n^2)."],"practical":"Reversing a string in place with two pointers (start and end, swapping and moving inward) avoids the O(n) extra space a naive new-string approach would use.","examples":[{"lang":"python","code":"def reverse(s):\n    s = list(s)\n    left, right = 0, len(s) - 1\n    while left < right:\n        s[left], s[right] = s[right], s[left]\n        left += 1\n        right -= 1\n    return ''''.join(s)"}],"mistakes":["Using repeated string concatenation in a loop, which is O(n^2) in many languages due to immutability.","Off-by-one errors at array boundaries — always double-check inclusive vs exclusive indices."],"important":["Two-pointer technique is a common O(n) pattern for sorted arrays or palindrome checks.","Dynamic arrays (like Python lists, Java ArrayList) amortize resizing cost to O(1) per append on average."]}'::jsonb,
   0, 25, '{}')
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-linkedlists', 'dsa', 'Linked Lists', 'Singly/doubly linked nodes and pointer manipulation.',
   '{"intro":"A linked list trades an array''s fast random access for O(1) insertion/deletion at known positions, by chaining nodes together with pointers instead of storing data contiguously.","concepts":["A singly linked list node holds data and a pointer to the next node; a doubly linked list also points backward.","Insertion/deletion at a known node is O(1); finding that node in the first place is O(n).","The classic ''fast and slow pointer'' technique detects cycles and finds the middle node in one pass."],"practical":"Detecting a cycle in a linked list with Floyd''s algorithm uses two pointers moving at different speeds — if they ever meet, a cycle exists, all without extra memory for a visited-set.","examples":[{"lang":"python","code":"class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\ndef has_cycle(head):\n    slow, fast = head, head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n        if slow == fast:\n            return True\n    return False"}],"mistakes":["Losing the reference to the rest of the list while reassigning .next during insertion/deletion.","Forgetting to update the tail pointer when appending to a list that tracks one."],"important":["Linked lists have O(n) access time, unlike an array''s O(1).","Doubly linked lists allow O(1) removal given just a node reference, without needing the previous node."]}'::jsonb,
   1, 30, ARRAY['dsa-arrays']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-stacks-queues', 'dsa', 'Stacks and Queues', 'LIFO and FIFO structures and their classic use cases.',
   '{"intro":"Stacks and queues restrict how you access a collection — LIFO (last in, first out) versus FIFO (first in, first out) — and that restriction is exactly what makes them useful for specific algorithmic patterns.","concepts":["A stack supports push/pop from one end only; used in function call stacks, undo systems, and expression parsing.","A queue supports enqueue at the back and dequeue from the front; used in BFS and task scheduling.","A balanced-parentheses checker is a classic stack problem: push on open bracket, pop and match on close."],"practical":"The browser''s back button is a stack: each visited page is pushed, and ''back'' pops the most recent one — while a print queue is FIFO, printing jobs in the order they were submitted.","examples":[{"lang":"python","code":"def is_balanced(expr):\n    stack = []\n    pairs = {'')'': ''('', '']'': ''['', ''}'': ''{''}\n    for ch in expr:\n        if ch in ''([{'':\n            stack.append(ch)\n        elif ch in '')]}'':\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack"}],"mistakes":["Using a plain list as a queue with pop(0), which is O(n) — use collections.deque instead for O(1).","Forgetting to check if the stack is empty before popping, causing an error."],"important":["BFS (breadth-first search) uses a queue; DFS (depth-first search) uses a stack (or recursion).","collections.deque in Python gives O(1) appends/pops from both ends."]}'::jsonb,
   2, 35, ARRAY['dsa-linkedlists']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-trees', 'dsa', 'Trees', 'Binary trees, BSTs, and traversal strategies.',
   '{"intro":"Trees model hierarchical relationships — file systems, org charts, decision logic — and binary search trees specifically keep data ordered for fast search, insert, and delete.","concepts":["A Binary Search Tree keeps left-subtree values smaller and right-subtree values larger than the node.","In-order traversal of a BST visits nodes in sorted order; pre-order and post-order serve other purposes (like copying or deleting a tree).","A balanced BST gives O(log n) search/insert/delete; an unbalanced one can degrade to O(n)."],"practical":"Searching a balanced BST of a million nodes takes about 20 comparisons (log2(1,000,000) ≈ 20), versus up to a million comparisons in an unbalanced, list-like tree.","examples":[{"lang":"python","code":"class Node:\n    def __init__(self, val):\n        self.val = val\n        self.left = self.right = None\n\ndef insert(root, val):\n    if root is None:\n        return Node(val)\n    if val < root.val:\n        root.left = insert(root.left, val)\n    else:\n        root.right = insert(root.right, val)\n    return root"}],"mistakes":["Inserting already-sorted data into a plain BST without balancing, degrading it into a linked list.","Confusing in-order, pre-order, and post-order traversal outputs."],"important":["Self-balancing trees (AVL, Red-Black) guarantee O(log n) operations even in the worst case.","In-order traversal of a BST always yields values in ascending order."]}'::jsonb,
   3, 40, ARRAY['dsa-stacks-queues']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-graphs', 'dsa', 'Graphs', 'Modeling networks with vertices, edges, and traversal algorithms.',
   '{"intro":"Graphs generalize trees to model any network of relationships — social connections, road maps, dependency chains — using vertices (nodes) and edges (connections) that can be directed, weighted, or both.","concepts":["Graphs can be represented as an adjacency list (space-efficient for sparse graphs) or adjacency matrix (fast edge lookups, O(V^2) space).","BFS finds the shortest path in an unweighted graph; DFS is used for cycle detection and topological sorting.","Dijkstra''s algorithm finds shortest paths in a weighted graph with non-negative edge weights."],"practical":"A course-prerequisite system is a directed graph; topological sort (via DFS) determines a valid order to take courses such that every prerequisite comes before the course that needs it.","examples":[{"lang":"python","code":"def bfs(graph, start):\n    visited, queue, order = {start}, [start], []\n    while queue:\n        node = queue.pop(0)\n        order.append(node)\n        for neighbor in graph[node]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n    return order"}],"mistakes":["Forgetting to mark nodes as visited, causing infinite loops in cyclic graphs.","Using BFS when the graph is weighted and shortest path (not fewest edges) is required — Dijkstra''s is needed instead."],"important":["BFS uses a queue; DFS uses a stack or recursion.","A topological sort is only possible on a Directed Acyclic Graph (DAG)."]}'::jsonb,
   4, 45, ARRAY['dsa-trees']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('dsa-sorting', 'dsa', 'Sorting and Searching', 'Comparison sorts, binary search, and complexity trade-offs.',
   '{"intro":"Sorting and searching are the most-used algorithmic building blocks in software — and comparing their time/space trade-offs is a staple of technical interviews and real system design alike.","concepts":["Comparison sorts (merge sort, quicksort) run in O(n log n) average case; bubble/insertion sort are O(n^2).","Binary search on a sorted array runs in O(log n), but requires the data to already be sorted.","Merge sort guarantees O(n log n) worst case and is stable; quicksort averages O(n log n) but can degrade to O(n^2)."],"practical":"Searching a sorted list of a million entries takes about 20 comparisons with binary search, versus up to a million with linear search — the difference is the entire reason databases maintain sorted indexes.","examples":[{"lang":"python","code":"def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1"}],"mistakes":["Running binary search on an unsorted array, which produces incorrect results silently.","Choosing quicksort for data that''s already nearly sorted without a good pivot strategy, risking O(n^2)."],"important":["Binary search requires sorted input — always check this precondition.","Stable sorts preserve the relative order of equal elements; this matters when sorting by multiple keys."]}'::jsonb,
   5, 50, ARRAY['dsa-graphs']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-fundamentals', 'c', 'C Fundamentals', 'Variables, types, and the compile-link-run cycle.',
   '{"intro":"C gives you almost no safety net and almost no abstraction — which is exactly why understanding it builds a mental model of what''s really happening under the hood in higher-level languages.","concepts":["C requires explicit type declarations; there''s no dynamic typing or automatic garbage collection.","A C program goes through preprocessing, compilation, assembly, and linking to produce an executable.","printf/scanf use format specifiers (%d, %f, %s, %c) that must match the argument''s actual type."],"practical":"Mismatching a format specifier — like using %d for a float — doesn''t raise a compile error in classic C; it produces undefined behavior, often garbage output.","examples":[{"lang":"c","code":"#include <stdio.h>\n\nint main() {\n    int score = 92;\n    float average = score / 2.0f;\n    printf(\"Average: %.1f\\n\", average);\n    return 0;\n}"}],"mistakes":["Forgetting to include a needed header (like <stdio.h>) and getting an implicit-declaration warning.","Using the wrong format specifier in printf/scanf, causing garbage values or crashes."],"important":["main() should return an int, conventionally 0 for success.","C has no built-in string type — strings are arrays of char terminated by ''\\0''."]}'::jsonb,
   0, 25, '{}')
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-functions', 'c', 'Functions', 'Function declarations, parameters, and pass-by-value semantics.',
   '{"intro":"C functions are strictly pass-by-value — understanding exactly what gets copied (and what doesn''t) is essential before pointers make everything more flexible.","concepts":["A function must be declared (prototype) before use if defined later in the file, or the compiler assumes int.","Arguments are passed by value — the function gets a copy, so changes inside don''t affect the caller''s variable.","Arrays are the exception: passing an array actually passes a pointer to its first element."],"practical":"Writing a swap(int a, int b) function that swaps its parameters has zero effect on the caller''s variables, because a and b are local copies — this is the classic motivation for introducing pointers.","examples":[{"lang":"c","code":"int square(int x) {\n    return x * x;\n}\n\nint main() {\n    int n = 5;\n    printf(\"%d\\n\", square(n)); // n itself is unchanged\n    return 0;\n}"}],"mistakes":["Expecting a function to modify a caller''s plain variable without using a pointer parameter.","Forgetting a function prototype, causing the compiler to assume a default int return type."],"important":["To modify a caller''s variable, a function needs a pointer parameter (e.g. int *x).","Arrays passed to functions decay to pointers, losing their original size information."]}'::jsonb,
   1, 30, ARRAY['c-fundamentals']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-pointers', 'c', 'Pointers', 'Memory addresses, dereferencing, and pointer arithmetic.',
   '{"intro":"Pointers are C''s defining feature — variables that store memory addresses instead of values directly — enabling dynamic memory, efficient array passing, and data structures like linked lists.","concepts":["''&'' gets the address of a variable; ''*'' dereferences a pointer to access the value it points to.","Pointer arithmetic is scaled by the pointed-to type''s size (ptr + 1 moves by sizeof(type) bytes).","A NULL pointer points to nothing; dereferencing it is undefined behavior (typically a crash)."],"practical":"Passing &variable to scanf is required precisely because scanf needs the address to write the input value into — without it, scanf would only get a copy and couldn''t modify the caller''s variable.","examples":[{"lang":"c","code":"int x = 10;\nint *p = &x;\n*p = 20; // modifies x through the pointer\nprintf(\"%d\\n\", x); // prints 20"}],"mistakes":["Dereferencing an uninitialized or NULL pointer, causing undefined behavior or a crash.","Confusing ''*'' in a declaration (int *p) with ''*'' as the dereference operator in an expression."],"important":["Always initialize pointers, even to NULL, to avoid dereferencing garbage addresses.","sizeof(pointer) gives the pointer''s own size (e.g. 8 bytes on 64-bit), not the pointed-to data''s size."]}'::jsonb,
   2, 35, ARRAY['c-functions']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-arrays-strings', 'c', 'Arrays and Strings', 'Fixed-size arrays and null-terminated character arrays.',
   '{"intro":"C arrays are fixed-size, contiguous, and offer no bounds checking — meaning it''s entirely your responsibility to stay within their limits, especially with strings.","concepts":["An array''s size must be known at compile time (for a plain array) or allocated dynamically.","A C string is a char array ending in ''\\0''; string.h functions like strlen/strcpy rely on that terminator.","Out-of-bounds array access is not checked by the compiler or runtime — it''s undefined behavior."],"practical":"strcpy(dest, src) will happily write past the end of dest if src is longer, silently corrupting adjacent memory — this class of bug is the root of countless real-world security vulnerabilities.","examples":[{"lang":"c","code":"#include <string.h>\n\nchar name[20];\nstrcpy(name, \"LearnQwik\");\nprintf(\"%s has length %lu\\n\", name, strlen(name));"}],"mistakes":["Using strcpy/strcat without checking destination buffer size, risking a buffer overflow.","Forgetting the extra byte needed for ''\\0'' when sizing a character array."],"important":["Prefer strncpy or bounds-checked alternatives over raw strcpy where input size isn''t guaranteed.","C performs no automatic array bounds checking — this is a common source of memory bugs."]}'::jsonb,
   3, 40, ARRAY['c-pointers']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-structures', 'c', 'Structures and Unions', 'Grouping related data and understanding memory layout differences.',
   '{"intro":"Structures let you group related fields into one custom type — the closest thing C has to an object — while unions share memory between fields for a different, more specialized purpose.","concepts":["A struct allocates separate memory for each field; total size is roughly the sum (plus padding).","A union allocates one shared memory block sized for its largest member — only one field is valid at a time.","Access struct/union fields via ''.'' for a value or ''->'' via a pointer."],"practical":"A struct Student {char name[50]; int id; float gpa;} models a database-style record naturally, with each field independently readable, unlike a union where writing to one field overwrites the others'' memory.","examples":[{"lang":"c","code":"struct Student {\n    char name[50];\n    int id;\n    float gpa;\n};\n\nstruct Student s1 = {\"Aisha\", 101, 8.7f};\nprintf(\"%s: %.1f\\n\", s1.name, s1.gpa);"}],"mistakes":["Using a union expecting all fields to hold valid data simultaneously — they share memory, so they can''t.","Forgetting ''->'' when accessing struct fields through a pointer instead of ''.''."],"important":["sizeof a struct can be larger than the sum of its fields due to memory alignment padding.","A union''s size equals its largest member''s size, not the sum of all members."]}'::jsonb,
   4, 45, ARRAY['c-arrays-strings']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;
insert into topics (id, subject_id, name, description, content, position, estimated_minutes, prerequisite_topic_ids) values
  ('c-files-memory', 'c', 'File Handling and Dynamic Memory', 'File I/O with FILE* and manual memory management with malloc/free.',
   '{"intro":"C gives you direct control over both files and memory — with fopen/fread/fwrite for I/O, and malloc/free for the heap — and with that control comes full responsibility for cleaning up after yourself.","concepts":["fopen(path, mode) returns a FILE* (or NULL on failure); always check for NULL before using it.","malloc(size) allocates raw heap memory; free(ptr) releases it — every malloc needs a matching free.","Forgetting free() causes a memory leak; calling free() twice on the same pointer is undefined behavior."],"practical":"A program that allocates a growing array with malloc/realloc as it reads unknown-length input must track size carefully, since forgetting to realloc before writing leads straight to buffer overflows.","examples":[{"lang":"c","code":"int *arr = malloc(5 * sizeof(int));\nif (arr == NULL) {\n    return 1; // allocation failed\n}\nfor (int i = 0; i < 5; i++) arr[i] = i * i;\nfree(arr);\narr = NULL;"}],"mistakes":["Not checking malloc''s return value for NULL before using the pointer.","Using a pointer after calling free() on it (a ''use-after-free'' bug) or freeing it twice."],"important":["Set a pointer to NULL after freeing it to avoid accidental use-after-free bugs.","Always close files with fclose() once done, mirroring malloc/free discipline."]}'::jsonb,
   5, 50, ARRAY['c-structures']::text[])
on conflict (id) do update set
  subject_id = excluded.subject_id, name = excluded.name,
  description = excluded.description, content = excluded.content,
  position = excluded.position, estimated_minutes = excluded.estimated_minutes,
  prerequisite_topic_ids = excluded.prerequisite_topic_ids;

-- ---------- QUESTIONS ----------
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-fundamentals-q1', 'java-fundamentals', 'What does the JVM execute?', '["Raw .java source files","Platform-independent bytecode","Machine code compiled for your exact CPU","Python-compatible IR"]'::jsonb, 1,
   'javac compiles source into bytecode, which the JVM interprets or JIT-compiles.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-fundamentals-q2', 'java-fundamentals', 'What is the result of 7 / 2 in Java, where both operands are int?', '["3.5","3","4","Compile error"]'::jsonb, 1,
   'Integer division truncates toward zero, so 7 / 2 evaluates to 3.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-fundamentals-q3', 'java-fundamentals', 'Which comparison correctly checks String content equality?', '["a == b","a.equals(b)","a.same(b)","a === b"]'::jsonb, 1,
   '== compares references for objects; .equals() compares the actual characters.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-fundamentals-q4', 'java-fundamentals', 'Which of these is NOT a Java primitive type?', '["int","String","boolean","char"]'::jsonb, 1,
   'String is a reference type (an object), not a primitive.', 'Medium', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-fundamentals-q5', 'java-fundamentals', 'What happens when you narrow a long to an int without an explicit cast?', '["It compiles and rounds automatically","Compile-time error","Runtime exception","Silent data loss with no warning"]'::jsonb, 1,
   'Narrowing conversions require an explicit cast in Java; otherwise the compiler rejects it.', 'Hard', 4)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-oop-q1', 'java-oop', 'What is the relationship between a class and an object?', '["They''re the same thing","A class is an instance of an object","An object is an instance of a class","A class contains many objects internally"]'::jsonb, 2,
   'A class defines structure and behavior; an object is a concrete instance of it.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-oop-q2', 'java-oop', 'Why make fields private and add getters/setters?', '["It''s required by the compiler","To enable encapsulation and control access","It makes code run faster","Private fields use less memory"]'::jsonb, 1,
   'Encapsulation protects internal state from invalid external modification.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-oop-q3', 'java-oop', 'What is constructor overloading?', '["Having multiple constructors with different parameter lists","Calling a constructor more than once","A constructor that throws an exception","Inheriting a constructor from a superclass"]'::jsonb, 0,
   'Overloaded constructors let a class be built in more than one way.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-oop-q4', 'java-oop', 'What return type does a constructor have?', '["void","The class type","int","None — constructors have no return type"]'::jsonb, 3,
   'Constructors never declare a return type, unlike regular methods.', 'Medium', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-inheritance-q1', 'java-inheritance', 'What keyword establishes inheritance between two classes?', '["implements","extends","inherits","super"]'::jsonb, 1,
   'A class uses ''extends'' to inherit from a single superclass.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-inheritance-q2', 'java-inheritance', 'What is dynamic dispatch?', '["Choosing which overloaded method to call at compile time","Deciding which overridden method runs based on the object''s actual runtime type","A way to allocate memory dynamically","Randomly selecting a method to execute"]'::jsonb, 1,
   'The JVM resolves overridden methods based on the real object type at runtime.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-inheritance-q3', 'java-inheritance', 'How many classes can a Java class directly extend?', '["Unlimited","Two","One","Zero"]'::jsonb, 2,
   'Java allows single inheritance for classes; multiple inheritance is achieved via interfaces.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-inheritance-q4', 'java-inheritance', 'Can a private method be overridden in a subclass?', '["Yes, always","No — it''s hidden, not overridden","Only if marked final","Only in the same package"]'::jsonb, 1,
   'Private methods aren''t inherited in the polymorphic sense, so subclasses can only define a new, unrelated method with the same name.', 'Hard', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-exceptions-q1', 'java-exceptions', 'Which exceptions must be either caught or declared with ''throws''?', '["RuntimeException subclasses","Checked exceptions","Errors","All exceptions equally"]'::jsonb, 1,
   'Checked exceptions are enforced by the compiler; unchecked ones are not.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-exceptions-q2', 'java-exceptions', 'When does a finally block execute?', '["Only if an exception is thrown","Only if no exception is thrown","Always, regardless of exceptions","Only if the catch block also runs"]'::jsonb, 2,
   'finally runs whether the try block succeeds, fails, or even returns early.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-exceptions-q3', 'java-exceptions', 'What''s wrong with ordering catch(Exception e) before catch(IOException e)?', '["Nothing, it''s valid and fine","It''s a compile error — the more general catch makes the specific one unreachable","It runs both catch blocks","It silently ignores IOException"]'::jsonb, 1,
   'Java requires more specific exception types to be caught before more general ones.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-exceptions-q4', 'java-exceptions', 'What''s the benefit of try-with-resources?', '["Faster exception handling","Automatically closes AutoCloseable resources","Allows skipping catch blocks entirely","Prevents all runtime exceptions"]'::jsonb, 1,
   'Resources declared in the try parentheses are closed automatically when the block exits.', 'Medium', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-collections-q1', 'java-collections', 'Which collection type does NOT allow duplicate elements?', '["List","Set","Map values","Array"]'::jsonb, 1,
   'Set enforces uniqueness of its elements by contract.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-collections-q2', 'java-collections', 'What is the average time complexity of a HashMap.get() call?', '["O(n)","O(log n)","O(1)","O(n^2)"]'::jsonb, 2,
   'HashMap achieves average O(1) lookups via hashing, assuming a good hash distribution.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-collections-q3', 'java-collections', 'Which List implementation gives faster random access via index?', '["LinkedList","ArrayList","Both are equal","Neither supports indexing"]'::jsonb, 1,
   'ArrayList is backed by an array, so indexed access is O(1); LinkedList must traverse nodes.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-collections-q4', 'java-collections', 'What must you override together when using a custom class as a HashMap key?', '["toString() and clone()","equals() and hashCode()","compareTo() and toString()","Nothing — it works by default"]'::jsonb, 1,
   'Inconsistent equals()/hashCode() breaks HashMap lookups and causes duplicate-looking entries.', 'Hard', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-multithreading-q1', 'java-multithreading', 'Why is implementing Runnable often preferred over extending Thread?', '["Runnable runs faster","Java allows only single class inheritance, so Runnable keeps that slot free","Thread cannot be started twice","Runnable is required by the compiler"]'::jsonb, 1,
   'Implementing an interface preserves the ability to extend another class if needed.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-multithreading-q2', 'java-multithreading', 'What causes a race condition?', '["Too many threads running at once","Unsynchronized concurrent access to shared mutable state","Using too much memory","Slow disk I/O"]'::jsonb, 1,
   'Race conditions arise when threads interleave reads/writes to shared data without coordination.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-multithreading-q3', 'java-multithreading', 'Is the ++ operator atomic in Java?', '["Yes, always","No — it''s three separate steps that can interleave across threads","Only for int, not other types","Only inside synchronized blocks"]'::jsonb, 1,
   '++ involves reading, incrementing, and writing back — not a single atomic operation.', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('java-multithreading-q4', 'java-multithreading', 'What is a deadlock?', '["A thread that runs forever","Two or more threads waiting on locks the others hold, with no progress possible","A thread crashing due to an exception","A memory leak in threaded code"]'::jsonb, 1,
   'Deadlock is a circular wait condition between threads holding each other''s needed locks.', 'Hard', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-fundamentals-q1', 'python-fundamentals', 'What defines a code block in Python?', '["Curly braces","Indentation","The ''begin''/''end'' keywords","Semicolons"]'::jsonb, 1,
   'Python uses consistent indentation instead of braces to delimit blocks.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-fundamentals-q2', 'python-fundamentals', 'What does b = a do if ''a'' is a list?', '["Creates a deep copy of the list","Creates a second reference to the same list object","Raises a TypeError","Converts the list to a tuple"]'::jsonb, 1,
   'Assignment binds a new name to the same object; both names point to one list in memory.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-fundamentals-q3', 'python-fundamentals', 'Which is the modern way to format a string with a variable''s value?', '["\"Value: \" + str(x)","\"Value: %s\" % x","f\"Value: {x}\"","\"Value: \".format(x)"]'::jsonb, 2,
   'f-strings are the concise, readable, and now-standard formatting approach.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-fundamentals-q4', 'python-fundamentals', 'What is ''duck typing'' in Python?', '["A strict type-checking system","Code that works with any object supporting the required operations, regardless of its declared type","A naming convention for functions","A debugging technique"]'::jsonb, 1,
   'Duck typing means Python cares about behavior (''if it quacks like a duck'') rather than explicit type.', 'Hard', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-functions-q1', 'python-functions', 'What does a function return if it has no explicit return statement?', '["0","An empty string","None","A runtime error"]'::jsonb, 2,
   'Python functions implicitly return None when no return statement executes.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-functions-q2', 'python-functions', 'What''s the danger of def f(x=[]):?', '["It''s a syntax error","The default list is shared and mutated across every call","It runs slower than other defaults","It can only be called once"]'::jsonb, 1,
   'Default arguments are evaluated once at definition time, so mutable defaults persist state between calls.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-functions-q3', 'python-functions', 'What does **kwargs collect inside a function?', '["A list of positional arguments","A dictionary of keyword arguments","A tuple of all arguments","Nothing — it''s a syntax error"]'::jsonb, 1,
   '**kwargs gathers any extra keyword arguments into a dict.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-oop-q1', 'python-oop', 'What is ''self'' in a Python instance method?', '["A reserved keyword like ''this'' in other languages, required by name","A reference to the current instance, by convention named self","An optional parameter","A global variable"]'::jsonb, 1,
   '''self'' isn''t a keyword — it''s a strong convention for the instance reference, which Python passes automatically.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-oop-q2', 'python-oop', 'Which method controls what print(obj) shows?', '["__repr__","__print__","__str__","__display__"]'::jsonb, 2,
   '__str__ defines the readable string representation used by print() and str().', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-oop-q3', 'python-oop', 'Does Python support multiple inheritance?', '["No, only single inheritance","Yes, directly via class C(A, B)","Only through interfaces","Only in Python 2"]'::jsonb, 1,
   'Python allows a class to inherit from multiple base classes directly.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-files-q1', 'python-files', 'What does the ''with'' statement guarantee for file handling?', '["Faster reads","The file is automatically closed even if an exception occurs","The file is opened in binary mode","The file contents are cached"]'::jsonb, 1,
   'Context managers guarantee cleanup code runs on exit, exception or not.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-files-q2', 'python-files', 'Which mode overwrites an existing file''s contents?', '["''a''","''r''","''w''","''x''"]'::jsonb, 2,
   '''w'' truncates the file first; ''a'' appends without erasing.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-files-q3', 'python-files', 'What happens if you open a file with mode ''w'' by mistake instead of ''a''?', '["Nothing, both behave the same","Existing content is erased before writing","It raises a FileExistsError","It appends automatically"]'::jsonb, 1,
   '''w'' mode truncates the file to zero length before writing.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-exceptions-q1', 'python-exceptions', 'When does the ''else'' clause of a try block execute?', '["Only when an exception is caught","Only when no exception occurs in the try block","Always, after finally","Never — Python try blocks have no else"]'::jsonb, 1,
   '''else'' runs only if the try block completes without raising.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-exceptions-q2', 'python-exceptions', 'What''s risky about a bare ''except:'' clause?', '["It''s a syntax error in Python 3","It also catches system-exiting exceptions like KeyboardInterrupt","It only catches ValueError","It silently continues without stopping the program"]'::jsonb, 1,
   'Bare except catches everything under BaseException, including exceptions meant to stop the program.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-exceptions-q3', 'python-exceptions', 'What should a custom exception typically subclass?', '["BaseException","Exception","object","RuntimeError only"]'::jsonb, 1,
   'Exception is the conventional base for user-defined exceptions, leaving system-exiting exceptions untouched.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-numpy-q1', 'python-numpy', 'What is the main performance advantage of NumPy arrays over Python lists?', '["They use less disk space","Vectorized operations run in optimized C code instead of Python loops","They support more data types","They are easier to print"]'::jsonb, 1,
   'NumPy pushes loop execution into compiled C, avoiding Python''s per-element interpreter overhead.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-numpy-q2', 'python-numpy', 'Does slicing a NumPy array create a copy or a view?', '["Always a copy","Always a view (shares memory)","A copy only for 1D arrays","It depends on array size"]'::jsonb, 1,
   'NumPy slices are views by default; use .copy() for an independent array.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('python-numpy-q3', 'python-numpy', 'What does arr[arr > 85] do?', '["Raises an error","Returns elements of arr greater than 85 (boolean masking)","Sorts the array descending","Replaces values over 85 with 85"]'::jsonb, 1,
   'Boolean masking filters an array using a condition applied element-wise.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-fundamentals-q1', 'dbms-fundamentals', 'What does the ''A'' in ACID stand for?', '["Availability","Atomicity","Access","Authentication"]'::jsonb, 1,
   'Atomicity means a transaction either fully completes or has no effect at all.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-fundamentals-q2', 'dbms-fundamentals', 'What is ''data independence'' in a DBMS?', '["Data never changes","Applications don''t need to know the physical storage layout","Each table is stored in a separate database","Users can''t share data"]'::jsonb, 1,
   'Data independence decouples how data is physically stored from how applications access it logically.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-fundamentals-q3', 'dbms-fundamentals', 'Why is a flat CSV file a poor substitute for a DBMS in a multi-user app?', '["CSV files can''t store numbers","No concurrency control or referential integrity across related data","CSV files are always larger","SQL can''t read CSV files at all"]'::jsonb, 1,
   'Flat files lack safe concurrent writes and enforce no relationships between records.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-er-model-q1', 'dbms-er-model', 'How is a many-to-many relationship implemented relationally?', '["A foreign key on the ''many'' side only","A junction table holding foreign keys to both entities","Two separate primary keys in one table","It can''t be represented relationally"]'::jsonb, 1,
   'A bridge/junction table is the standard way to represent many-to-many relationships.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-er-model-q2', 'dbms-er-model', 'What is required of a primary key?', '["It must be a number","It must be unique and non-null","It must reference another table","It must be named ''id''"]'::jsonb, 1,
   'Primary keys uniquely identify rows and cannot contain NULL.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-er-model-q3', 'dbms-er-model', 'What does a foreign key enforce?', '["Data compression","Referential integrity between related tables","Faster query execution always","Automatic indexing"]'::jsonb, 1,
   'Foreign keys ensure referenced rows in another table actually exist.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-sql-q1', 'dbms-sql', 'What''s the difference between WHERE and HAVING?', '["They''re interchangeable","WHERE filters before aggregation, HAVING filters after","HAVING is faster than WHERE","WHERE only works with JOINs"]'::jsonb, 1,
   'HAVING is needed specifically because WHERE cannot filter on aggregate function results.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-sql-q2', 'dbms-sql', 'Which JOIN returns all rows from the left table, with NULLs where there''s no match?', '["INNER JOIN","RIGHT JOIN","LEFT JOIN","CROSS JOIN"]'::jsonb, 2,
   'LEFT JOIN preserves every row from the left table regardless of a match.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-sql-q3', 'dbms-sql', 'What does GROUP BY do?', '["Sorts rows alphabetically","Combines rows sharing a value so aggregate functions can summarize them","Removes duplicate rows","Joins two tables"]'::jsonb, 1,
   'GROUP BY buckets rows by shared column values, enabling per-group aggregation.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-sql-q4', 'dbms-sql', 'What is DISTINCT used for?', '["Sorting results","Removing duplicate rows from output","Filtering NULL values","Joining tables"]'::jsonb, 1,
   'DISTINCT collapses duplicate rows in the result set.', 'Easy', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-normalization-q1', 'dbms-normalization', 'What does 1NF require?', '["No foreign keys","All column values must be atomic, with no repeating groups","Every table must have exactly one column","All data must be numeric"]'::jsonb, 1,
   '1NF is about eliminating multi-valued or repeating attributes in a single column.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-normalization-q2', 'dbms-normalization', 'What kind of dependency does 3NF eliminate?', '["Partial dependency","Transitive dependency","Circular dependency","Foreign key dependency"]'::jsonb, 1,
   '3NF removes cases where a non-key attribute depends on another non-key attribute.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-normalization-q3', 'dbms-normalization', 'What is a downside of over-normalizing a schema?', '["Data becomes inconsistent","Queries may require many joins, hurting read performance","Storage space always increases","Primary keys become optional"]'::jsonb, 1,
   'Highly normalized schemas can require complex, expensive joins for common reads.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-transactions-q1', 'dbms-transactions', 'What is a ''dirty read''?', '["Reading corrupted data from disk","Reading another transaction''s uncommitted changes","Reading the same row twice","A query that returns no rows"]'::jsonb, 1,
   'A dirty read happens when a transaction sees uncommitted changes from another transaction.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-transactions-q2', 'dbms-transactions', 'Which isolation level provides the strongest consistency guarantees?', '["Read Uncommitted","Read Committed","Repeatable Read","Serializable"]'::jsonb, 3,
   'Serializable enforces the strictest isolation, effectively as if transactions ran one at a time.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-transactions-q3', 'dbms-transactions', 'What does COMMIT do at the end of a transaction?', '["Undoes all changes","Makes all changes in the transaction permanent","Locks the table permanently","Deletes the transaction log"]'::jsonb, 1,
   'COMMIT finalizes the transaction''s changes, making them visible and durable.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-indexing-q1', 'dbms-indexing', 'What data structure do most database indexes use?', '["Linked list","B-tree","Hash map only","Binary search tree with no balancing"]'::jsonb, 1,
   'B-trees keep data sorted and balanced, giving efficient logarithmic lookups and range queries.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-indexing-q2', 'dbms-indexing', 'What''s a downside of adding many indexes to a table?', '["Reads become slower","Writes (INSERT/UPDATE/DELETE) become slower since indexes must be maintained","The table can no longer be queried","Indexes use no extra storage"]'::jsonb, 1,
   'Every index adds overhead to write operations that must keep the index up to date.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dbms-indexing-q3', 'dbms-indexing', 'What does the EXPLAIN command show?', '["The table''s schema","How the database plans to execute a query (e.g. index vs full scan)","A list of all indexes in the database","The query''s execution history"]'::jsonb, 1,
   'EXPLAIN reveals the query planner''s chosen execution strategy.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-arrays-q1', 'dsa-arrays', 'What is the time complexity of accessing an array element by index?', '["O(n)","O(log n)","O(1)","O(n^2)"]'::jsonb, 2,
   'Arrays support constant-time indexed access due to contiguous memory layout.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-arrays-q2', 'dsa-arrays', 'Why can repeated string concatenation in a loop be slow?', '["Strings can''t be concatenated in loops","Immutable strings require creating a new string each time, costing O(n) per operation","It always causes a memory leak","Only true in Python, not other languages"]'::jsonb, 1,
   'Each concatenation of an immutable string copies all existing characters, leading to O(n^2) total cost.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-arrays-q3', 'dsa-arrays', 'What technique efficiently reverses an array in place?', '["Recursion with extra arrays","Two pointers swapping from both ends toward the middle","Sorting the array first","Converting to a linked list"]'::jsonb, 1,
   'Two pointers moving inward swap elements without needing extra space.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-linkedlists-q1', 'dsa-linkedlists', 'What is the time complexity of inserting a node at a known position in a linked list?', '["O(n)","O(1)","O(log n)","O(n^2)"]'::jsonb, 1,
   'Once you have a reference to the node, relinking pointers is constant time.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-linkedlists-q2', 'dsa-linkedlists', 'What does Floyd''s cycle detection algorithm use?', '["A hash set of visited nodes","Two pointers moving at different speeds","Recursion with memoization","Sorting the list first"]'::jsonb, 1,
   'The ''tortoise and hare'' approach detects a cycle without extra memory.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-linkedlists-q3', 'dsa-linkedlists', 'What''s a downside of a linked list compared to an array?', '["Insertion is always slower","Random access by index is O(n) instead of O(1)","It can''t store duplicate values","It requires more code to declare"]'::jsonb, 1,
   'You must traverse from the head to reach a given index, unlike an array''s direct addressing.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-stacks-queues-q1', 'dsa-stacks-queues', 'Which traversal algorithm typically uses a queue?', '["Depth-first search","Breadth-first search","Binary search","Quicksort"]'::jsonb, 1,
   'BFS explores level by level, which a FIFO queue naturally supports.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-stacks-queues-q2', 'dsa-stacks-queues', 'Why is using a Python list''s pop(0) inefficient as a queue?', '["It''s actually O(1)","It''s O(n) because all remaining elements must shift","Lists can''t remove from the front","It only works for numbers"]'::jsonb, 1,
   'Removing the first element of a list requires shifting every remaining element.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-stacks-queues-q3', 'dsa-stacks-queues', 'What structure naturally checks for balanced parentheses?', '["Queue","Stack","Hash map","Binary tree"]'::jsonb, 1,
   'Pushing on open brackets and popping/matching on close brackets is a classic stack use.', 'Easy', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-trees-q1', 'dsa-trees', 'What does in-order traversal of a Binary Search Tree produce?', '["Random order","Values in ascending sorted order","Values in descending order","Only the leaf nodes"]'::jsonb, 1,
   'In-order (left, node, right) visits BST values in ascending order.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-trees-q2', 'dsa-trees', 'What happens if you insert already-sorted data into a plain (unbalanced) BST?', '["It stays perfectly balanced","It degrades into a structure like a linked list, with O(n) operations","It automatically rebalances","Insertion fails"]'::jsonb, 1,
   'Without balancing, sorted insertions create a skewed, list-like tree.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-trees-q3', 'dsa-trees', 'What is the average search time in a balanced BST with n nodes?', '["O(n)","O(log n)","O(1)","O(n log n)"]'::jsonb, 1,
   'Balanced BSTs halve the search space at each step, giving logarithmic time.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-graphs-q1', 'dsa-graphs', 'Which algorithm finds the shortest path in an unweighted graph?', '["DFS","BFS","Bubble sort","Binary search"]'::jsonb, 1,
   'BFS explores level by level, guaranteeing the shortest path in edge count for unweighted graphs.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-graphs-q2', 'dsa-graphs', 'What must be true of a graph for a topological sort to exist?', '["It must be undirected","It must be a Directed Acyclic Graph (DAG)","It must be weighted","It must have exactly one root"]'::jsonb, 1,
   'Topological ordering requires no cycles, since a cycle has no valid ''before/after'' order.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-graphs-q3', 'dsa-graphs', 'Why must visited nodes be tracked during graph traversal?', '["To save memory","To avoid infinite loops in graphs containing cycles","It''s optional for correctness","Only needed for weighted graphs"]'::jsonb, 1,
   'Without tracking visited nodes, a cyclic graph can cause traversal to loop forever.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-sorting-q1', 'dsa-sorting', 'What is the time complexity of binary search on a sorted array of n elements?', '["O(n)","O(log n)","O(n log n)","O(1)"]'::jsonb, 1,
   'Binary search halves the search space each step, giving logarithmic time.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-sorting-q2', 'dsa-sorting', 'What precondition does binary search require?', '["The array must contain only integers","The array must be sorted","The array must have an even length","The array must be a linked list"]'::jsonb, 1,
   'Binary search''s halving logic only works correctly on sorted data.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-sorting-q3', 'dsa-sorting', 'What is quicksort''s worst-case time complexity?', '["O(n log n)","O(n)","O(n^2)","O(log n)"]'::jsonb, 2,
   'With a poor pivot choice (e.g. already-sorted data with a naive pivot), quicksort degrades to O(n^2).', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('dsa-sorting-q4', 'dsa-sorting', 'What does it mean for a sorting algorithm to be ''stable''?', '["It never crashes","It preserves the relative order of equal elements","It always runs in O(n log n)","It sorts in place with no extra memory"]'::jsonb, 1,
   'Stability matters when sorting by one key while preserving prior ordering by another.', 'Medium', 3)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-fundamentals-q1', 'c-fundamentals', 'What terminates a C string?', '["A newline character","The null character ''\\0''","The end of the array''s allocated size","A special EOF marker"]'::jsonb, 1,
   'C strings are null-terminated char arrays; ''\0'' marks the end.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-fundamentals-q2', 'c-fundamentals', 'What are the stages a C program goes through to become an executable?', '["Only compilation","Preprocessing, compilation, assembly, linking","Interpretation only","Compilation then interpretation"]'::jsonb, 1,
   'The C toolchain runs the preprocessor, compiles to assembly, assembles to object code, then links.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-fundamentals-q3', 'c-fundamentals', 'What happens if you use %d in printf for a float argument?', '["It''s automatically converted correctly","Undefined behavior — often garbage output","A compile-time error","It prints as a string"]'::jsonb, 1,
   'printf trusts the format specifier; a mismatch produces undefined behavior since it reads the wrong number of bytes.', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-functions-q1', 'c-functions', 'How are arguments passed to functions in C by default?', '["By reference","By value — the function receives a copy","By pointer only","It depends on the type"]'::jsonb, 1,
   'C passes arguments by value; to modify the caller''s data you must pass a pointer explicitly.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-functions-q2', 'c-functions', 'What must you use to let a function modify a caller''s int variable?', '["Pass it normally","Pass a pointer to it","Declare it as static","It''s not possible in C"]'::jsonb, 1,
   'Passing a pointer lets the function dereference and modify the original memory location.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-functions-q3', 'c-functions', 'What happens to an array''s size information when passed to a function?', '["It''s preserved automatically","It decays to a pointer, losing the original size","The function receives a full copy of the array","C rejects passing arrays to functions"]'::jsonb, 1,
   'Arrays decay to a pointer to their first element, so sizeof inside the function won''t reflect the original array.', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-pointers-q1', 'c-pointers', 'What does the ''&'' operator do in C?', '["Dereferences a pointer","Gets the memory address of a variable","Performs bitwise AND only","Declares a new pointer"]'::jsonb, 1,
   '''&'' produces the address-of a variable, used to obtain a pointer to it.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-pointers-q2', 'c-pointers', 'Why does scanf require &variable instead of just variable?', '["It''s just a style convention","scanf needs the address to write the input value into the caller''s memory","& makes scanf run faster","It''s required only for strings"]'::jsonb, 1,
   'Since C is pass-by-value, scanf needs a pointer (address) to modify the original variable.', 'Medium', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-pointers-q3', 'c-pointers', 'What happens when you dereference a NULL pointer?', '["It returns 0 safely","Undefined behavior, typically a crash","It automatically allocates memory","It returns NULL again"]'::jsonb, 1,
   'NULL points to no valid memory, so dereferencing it is undefined behavior.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-arrays-strings-q1', 'c-arrays-strings', 'What character terminates every C string?', '["''\\n''","''\\0''","'' ''","EOF"]'::jsonb, 1,
   'The null character marks the end of a C string''s actual content.', 'Easy', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-arrays-strings-q2', 'c-arrays-strings', 'What is the danger of strcpy(dest, src) when src is longer than dest?', '["It truncates safely","It writes past dest''s bounds, corrupting memory (buffer overflow)","It throws a runtime exception","The compiler prevents this at compile time"]'::jsonb, 1,
   'C performs no bounds checking, so strcpy will overwrite adjacent memory if the destination is too small.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-arrays-strings-q3', 'c-arrays-strings', 'When declaring char name[20] for a 9-character word, why not use exactly char name[9]?', '["9 is an invalid array size","You need room for the terminating ''\\0'' character","Arrays must be a multiple of 4","It doesn''t matter either way"]'::jsonb, 1,
   'A 9-character string needs 10 bytes total to include the null terminator.', 'Medium', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-structures-q1', 'c-structures', 'How much memory does a union allocate?', '["The sum of all its members","Enough for its largest member only","A fixed 16 bytes always","Zero — unions are compile-time only"]'::jsonb, 1,
   'A union''s members share one memory region sized for the largest member.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-structures-q2', 'c-structures', 'How do you access a struct field through a pointer?', '["Using ''.''","Using ''->''","Using ''::''","Using ''&''"]'::jsonb, 1,
   'The arrow operator dereferences the pointer and accesses the field in one step.', 'Easy', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-structures-q3', 'c-structures', 'Why might sizeof(struct) exceed the sum of its individual field sizes?', '["It never does","Memory alignment padding between fields","Structs always double their size","Because of the struct''s name length"]'::jsonb, 1,
   'Compilers add padding so fields align to natural memory boundaries for performance.', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-files-memory-q1', 'c-files-memory', 'What should you check immediately after calling malloc?', '["Nothing, it always succeeds","Whether the returned pointer is NULL, indicating allocation failure","The exact byte count allocated","That the CPU has multiple cores"]'::jsonb, 1,
   'malloc can fail and return NULL when memory is unavailable; skipping this check risks crashes.', 'Medium', 0)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-files-memory-q2', 'c-files-memory', 'What is a ''use-after-free'' bug?', '["Using a pointer after it has been freed, accessing invalid memory","Freeing memory before allocating it","A compiler warning about unused variables","Forgetting to open a file before reading it"]'::jsonb, 0,
   'Accessing memory through a pointer after free() is undefined behavior and a common security bug.', 'Hard', 1)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;
insert into questions (id, topic_id, question, options, correct_index, explanation, difficulty, position) values
  ('c-files-memory-q3', 'c-files-memory', 'What does calling free() on the same pointer twice cause?', '["Nothing — it''s safe and idempotent","Undefined behavior, often a crash or memory corruption","The memory is allocated twice as large","A compile-time error"]'::jsonb, 1,
   'Double-free corrupts the heap''s internal bookkeeping and is undefined behavior.', 'Hard', 2)
on conflict (id) do update set
  topic_id = excluded.topic_id, question = excluded.question,
  options = excluded.options, correct_index = excluded.correct_index,
  explanation = excluded.explanation, difficulty = excluded.difficulty,
  position = excluded.position;

-- ---------- RESOURCES (recommendation engine pool) ----------
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r1', 'java-exceptions', 'Java Exceptions, Explained Simply', 'Article', 'Easy',
   8, 4.6, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r2', 'java-exceptions', 'Try/Catch Deep Dive', 'Video', 'Medium',
   14, 4.4, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r3', 'java-exceptions', 'Custom Exceptions Cheat Sheet', 'Cheat Sheet', 'Medium',
   4, 4.7, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r4', 'java-exceptions', 'Practice: 10 Exception Handling Drills', 'Practice', 'Hard',
   20, 4.5, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r5', 'java-collections', 'Java Collections Field Guide', 'Documentation', 'Medium',
   12, 4.5, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r6', 'java-collections', 'HashMap Internals Video Walkthrough', 'Video', 'Hard',
   18, 4.8, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r7', 'python-functions', 'Python Function Defaults: The Mutable Trap', 'Article', 'Medium',
   6, 4.6, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r8', 'python-numpy', 'NumPy Broadcasting Tutorial', 'Tutorial', 'Medium',
   15, 4.7, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r9', 'dbms-sql', 'SQL JOINs Visualized', 'Video', 'Easy',
   10, 4.9, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r10', 'dbms-normalization', 'Normalization Practice Set', 'Practice', 'Hard',
   25, 4.4, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r11', 'dsa-trees', 'Binary Search Trees, Step by Step', 'Tutorial', 'Medium',
   16, 4.7, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r12', 'dsa-graphs', 'Graph Traversal Cheat Sheet', 'Cheat Sheet', 'Medium',
   5, 4.6, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r13', 'c-pointers', 'Pointers Without Fear', 'Article', 'Medium',
   9, 4.5, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;
insert into resources (id, topic_id, title, type, difficulty, duration_minutes, rating, url) values
  ('r14', 'c-files-memory', 'malloc/free Discipline Drills', 'Practice', 'Hard',
   22, 4.5, NULL)
on conflict (id) do update set
  topic_id = excluded.topic_id, title = excluded.title, type = excluded.type,
  difficulty = excluded.difficulty, duration_minutes = excluded.duration_minutes,
  rating = excluded.rating, url = excluded.url;

commit;

-- Verify the seed loaded:
--   select (select count(*) from subjects)  as subjects,
--          (select count(*) from topics)    as topics,
--          (select count(*) from questions) as questions,
--          (select count(*) from resources) as resources;
-- Expected: 5 subjects, 30 topics, 100 questions, 14 resources.