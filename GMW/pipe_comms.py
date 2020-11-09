from multiprocessing import Process, Pipe, Queue

class Msg:
    def __init__(self, message, name):
        self.message = message
        self.name = name

class Person:
    def __init__(self, name):
        self.name = name

    def introduction(self, conn, q):
        if conn.poll():
            intro = conn.recv()
            q.put(intro)
            conn.send(Msg("Hi " + intro.name + "! I am " + str(self.name) + ". It's nice to meet you.", self.name))
        else:
            conn.send(Msg("Salutations! I am " + str(self.name) + ". What's your name?", self.name))
            response = conn.recv()
            q.put(response)

if __name__ == '__main__':
    a = Person("Alice")
    b = Person("Bob")
    parent_conn, child_conn = Pipe()
    q = Queue()
    p_a = Process(target=a.introduction, args=(parent_conn, q,))
    p_b = Process(target=b.introduction, args=(child_conn, q,))
    p_a.start()
    p_b.start()
    p_a.join()
    p_b.join()
    # should be 2 things in the queue
    print(q.get().message)
    print(q.get().message)