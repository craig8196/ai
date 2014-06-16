import numpy

class KalmanFilter(object):
    def __init__(self, std_dev_x=5, std_dev_y=5):
        self.covariance_initial = [0.07, 0.07, 30, 0.07, 0.07, 30]
        self.std_dev_x = std_dev_x
        self.std_dev_y = std_dev_y
        # covariance matrix of x and y
        self.sigma_z = numpy.matrix([[std_dev_x**2, 0],[0, std_dev_y**2]])
        # observation matrix, selects for the position
        self.H = numpy.matrix([[1,0,0,0,0,0],[0,0,0,1,0,0]])
        self.HT = self.H.T
        # covariance matrix for position, velocity, and acceleration for x and y
        self.sigma_x = numpy.zeros((6, 6))
        self.sigma_x[0, 0] = self.covariance_initial[0]
        self.sigma_x[1, 1] = self.covariance_initial[1]
        self.sigma_x[2, 2] = self.covariance_initial[2]
        self.sigma_x[3, 3] = self.covariance_initial[3]
        self.sigma_x[4, 4] = self.covariance_initial[4]
        self.sigma_x[5, 5] = self.covariance_initial[5]
        # initialize Newtonian physics matrix
        self.set_F()
        # covariance matrix for position, velocity, and acceleration for x and y
        self.sigma_t = numpy.zeros((6, 6))
        self.sigma_t[0, 0] = self.covariance_initial[0]
        self.sigma_t[1, 1] = self.covariance_initial[1]
        self.sigma_t[2, 2] = self.covariance_initial[2]
        self.sigma_t[3, 3] = self.covariance_initial[3]
        self.sigma_t[4, 4] = self.covariance_initial[4]
        self.sigma_t[5, 5] = self.covariance_initial[5]
        # the mean position vector
        self.mu_t = numpy.zeros((6, 1))
        # the identity matrix
        self.identity = numpy.zeros((6, 6))
        for i in range(self.identity.shape[0]):
            self.identity[i][i] = 1
        # keep track of total time change
        self.time_from_start = 0
        
    def set_F(self, delta_t=1, friction=0):
        self.F = numpy.zeros((6, 6))
        self.delta_t = delta_t
        self.friction = friction
        (x_len, y_len) = self.F.shape
        
        # set diagonal to 1
        for i in range(x_len):
            self.F[i, i] = 1
        F = self.F
        F[0, 1] = delta_t
        F[1, 2] = delta_t
        F[3, 4] = delta_t
        F[4, 5] = delta_t
        F[0, 2] = (delta_t**2)/2
        F[3, 5] = (delta_t**2)/2
        F[2, 1] = friction
        F[5, 4] = friction
        self.FT = self.F.T
    
    def add_time(self, time_amount):
        self.time_from_start += time_amount

    def predict(self):
        self.future_mu_t = self.F.dot(self.mu_t)
        return self.future_mu_t[0, 0], self.future_mu_t[3, 0]
    
    def get_positional_covariance_matrix(self):
        #~ return self.sigma_z
        sigma = numpy.matrix([[self.sigma_t[0,0], self.sigma_t[0,3]],
                              [self.sigma_t[3,0], self.sigma_t[3,3]]])
        return sigma
    
    def reset_covariance_matrix(self):
        # covariance matrix for position, velocity, and acceleration for x and y
        self.sigma_t = numpy.zeros((6, 6))
        self.sigma_t[0, 0] = self.covariance_initial[0]
        self.sigma_t[1, 1] = self.covariance_initial[1]
        self.sigma_t[2, 2] = self.covariance_initial[2]
        self.sigma_t[3, 3] = self.covariance_initial[3]
        self.sigma_t[4, 4] = self.covariance_initial[4]
        self.sigma_t[5, 5] = self.covariance_initial[5]
    
    def is_confident_in_position(self, std_dev=1.1):
        if abs(self.Z[0,0] - self.mu_t[0,0]) < math.sqrt(self.sigma_t[0,0])*(std_dev) and \
            abs(self.Z[1,0] - self.mu_t[3,0]) < math.sqrt(self.sigma_t[3,3])*(std_dev):
            return True
        return False
    
    def next_observed_z(self, x, y):
        """Return the predicted location of the tank, mu_t+1."""
        Z = numpy.zeros((2, 1))
        self.Z = Z
        Z[0, 0] = x
        Z[1, 0] = y
        # make common computation since the expression (F(sigma-t)FT + sigma-x) occurs three times
        common = self.F.dot(self.sigma_t).dot(self.FT) + self.sigma_x
        # make K + 1 computation
        K1 = common.dot(self.HT).dot((self.H.dot(common).dot(self.HT) + self.sigma_z).I)
        # make mu t + 1 computation, update previous variable
        self.mu_t = self.F.dot(self.mu_t) + K1.dot(Z - self.H.dot(self.F).dot(self.mu_t))
        # make sigma t + 1 computation, update previous variable
        self.sigma_t = (self.identity - K1.dot(self.H)).dot(common)
        self.add_time(self.delta_t)
        return self.mu_t[0, 0], self.mu_t[3, 0]
