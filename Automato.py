class Connection:
    def __init__(self):
        self.fruit_Name = []
        self.order_List = []

    def select(self):
        conn = pymysql.connect(host='localhost', user='root', password='automato', db='capstone', charset='utf8') 

        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql_fruit = "SELECT * FROM `Fruit`;" 
        sql_list = "SELECT * FROM `List`;"

        cursor.execute(sql_fruit) 
        res = cursor.fetchall() 

        for data in res:
            tmp = list(data.values())
            self.fruit_Name.append(tmp[0])
    
        cursor.execute(sql_list)
        res = cursor.fetchall()

        for data in res:
            self.order_List.append(data)

        conn.commit() 
        conn.close()
   
    def getFruitName(self):
        return self.fruit_Name
    
    def getOrderList(self):
        return self.order_List


class OrderManagement():
    def __init__(self, order_List):
        self.order_List = order_List
        self.sleep_Queue = []
        self.run_Queue = []
        self.change = {1:False, 2:False, 3:False}

    def sleepQueue(self):
        for element in self.order_List:
            self.sleep_Queue.append(element)

    def runQueue(self, num=0, port=0):
        if len(self.sleep_Queue) == 0:
            print('No more order')
            return
        
        if port == 0:
            for i in range(num):
                #del(self.sleep_Queue[0]['OrderNumber'])
                self.run_Queue.append(self.sleep_Queue[0])
                self.sleep_Queue = self.sleep_Queue[1:]
        else:
            del(self.run_Queue[port-1])
            #del(self.sleep_Queue[0]['OrderNumber'])
            self.run_Queue.insert(port-1, self.sleep_Queue[0])
            self.sleep_Queue = self.sleep_Queue[1:]

    def checkPackage(self, port):
        self.change[port] = True

    def getRunQueue(self):
        return self.run_Queue


class Status():
    def __init__(self, fruit_Detect, fruit_Name, run_Queue):
        self.fruit_Detect = fruit_Detect
        self.fruit_Name = fruit_Name
        self.run_Queue = run_Queue
        self.is_Fresh = False
        self.in_Order = False

    def checkFreshness(self):
        if self.fruit_Detect in self.fruit_Name:
            self.is_Fresh = True

    def checkOrderList(self):
        if self.is_Fresh:
            for i in range(3):
                if self.run_Queue[i][str(self.fruit_Detect)] > 0:
                    self.in_Order = True
                    break

    def getStatus(self):
        return self.is_Fresh, self.in_Order


class Distribution():
    def __init__(self, fruit_Detect, run_Queue, prior):
        self.fruit_Detect = fruit_Detect
        self.run_Queue = run_Queue
        self.prior = prior
        self.check_In = []
        self.consider_Priority = {}
        self.sorted_dict = {}
        self.cnt = 0
        self.val = 0
        self.ke = 0
        self.tmp1 = 0
        self.tmp2 = 0
        self.packaging = 0

    def plusPrior(self, ke):
        for i in range(1, 4):
            if i == ke:
                self.prior[i] = 0
            else:
                self.prior[i] += 1
        print(self.prior)

    def scheduling(self):
        # Find order that contain fruit_Detect
        # Scheduling
        # In case, use Aging(priority)
        for i in range(3):
            if self.run_Queue[i][str(self.fruit_Detect)] > 0:
                self.check_In.append(i)

        for check in self.check_In:
            if self.prior[check+1] > 3:
                self.consider_Priority[check+1] = self.prior[check+1]

        if len(self.consider_Priority) > 1:
            self.sorted_dict = sorted(self.consider_Priority.items(), key = lambda item:item[1], reverse=True)
            self.cnt = len(self.sorted_dict) - 1
            for i in range(len(self.sorted_dict)):
                if i == 0:
                    self.val = self.sorted_dict[i][1]
                    continue
                if self.val > self.sorted_dict[i][1]:
                    self.cnt = i - 1
                    break

            if self.cnt == 0:
                self.ke = self.sorted_dict[0][0]
                self.plusPrior(self.ke)
                self.run_Queue[self.ke-1][str(self.fruit_Detect)] -= 1

                return self.ke

            self.tmp1 = self.run_Queue[self.sorted_dict[0][0]-1]['OrderNumber']
            for i in range(1,self.cnt+1):
                self.tmp2 = self.run_Queue[self.sorted_dict[i][0]-1]['OrderNumber']
                if self.tmp1 > self.tmp2:
                    self.tmp1 = self.tmp2

            for i in range(3):
                if self.tmp1 == self.run_Queue[self.sorted_dict[i][0]-1]['OrderNumber']:
                    self.ke = self.sorted_dict[i][0]
                    break

            self.plusPrior(self.ke)
            self.run_Queue[self.ke-1][str(self.fruit_Detect)] -= 1

            return self.ke

        elif len(self.consider_Priority) == 1:
            self.ke = list(self.consider_Priority.keys())[0]
            self.plusPrior(self.ke)
            self.run_Queue[self.ke-1][str(self.fruit_Detect)] -= 1

            return self.ke

        else:
            for idx, check in enumerate(self.check_In):
                if idx == 0:
                    self.tmp1 = self.run_Queue[check]['OrderNumber']
                    continue
                self.tmp2 = self.run_Queue[check]['OrderNumber']
                if self.tmp1 > self.tmp2:
                    self.tmp1 = self.tmp2

            for check in self.check_In:
                if self.tmp1 == self.run_Queue[check]['OrderNumber']:
                    self.ke = check+1
                    break

            self.plusPrior(self.ke)
            self.run_Queue[self.ke-1][str(self.fruit_Detect)] -= 1

            return self.ke

    def decidePort(self, is_Fresh, in_Order):
        if is_Fresh == False:
            return 4
        elif is_Fresh == True and in_Order == False:
            return 5
        elif is_Fresh == True and in_Order == True:
            return self.scheduling()

    def finishPackage(self, port):
        for col in Distribution.getFruitName():
            if self.run_Queue[port-1][col] == 0:
                self.packaging += 1
        
        if self.packaging == 3:
            print('Port', self.port, 'Done')
            Distribution.RunQueue(self, 0, port)
            self.run_Queue = Distribution.getRunQueue()

    def getRunQueue(self):
        return self.run_Queue

    def getPrior(self):
        return self.prior

import pymysql

def main():
    # Connect Database and Receive Info
    conn = Connection()
    conn.select()
    fruit_Name = conn.getFruitName()
    order_List = conn.getOrderList()

    # Manage sleepQueue and runQueue
    orde = OrderManagement(order_List)
    orde.sleepQueue()
    orde.runQueue(3)
    run_Queue = orde.getRunQueue()
    print(run_Queue)

    prior= {1 : 0, 2 : 0, 3 : 0}

    run_Queue[0]['Apple'] = 1
    run_Queue[0]['Orange'] = 0

    cnt = 6
    while (cnt != 0):

    # Run Light-YOLOv4
    #mod = Model()
    #fruit_Detect = result()
        fruit_Detect = 'Apple'

    # Check Object's Status
        st = Status(fruit_Detect, fruit_Name, run_Queue)
        st.checkFreshness()
        st.checkOrderList()
        is_Fresh, in_Order = st.getStatus()

    # Consider Priority and Decide Port Number
        dis = Distribution(fruit_Detect, run_Queue, prior)
        port = dis.decidePort(is_Fresh, in_Order)
        prior = dis.getPrior()
        dis.finishPackage(port)
        run_Queue = dis.getRunQueue()
        print(run_Queue)
        print(port)

        cnt -= 1

    #[{'Apple': 3, 'Banana': 0, 'Orange': 2, 'OrderNumber': 1}, {'Apple': 5, 'Banana': 3, 'Orange': 0, 'OrderNumber': 2}, {'Apple': 2, 'Banana': 4, 'Orange': 4, 'OrderNumber': 3}]


if __name__ == '__main__':
    main()