#include "FusionEKF.h"
#include <iostream>
#include "Eigen/Dense"
#include "tools.h"

using Eigen::MatrixXd;
using Eigen::VectorXd;
using std::cout;
using std::endl;
using std::vector;

/**
 * Constructor.
 * 构造函数是一种特殊的成员函数，它的名字和类名相同，没有返回值，不需要用户调用（用户也不能调用），
 * 而是在创建对象时自动执行。构造函数的作用是在创建对象时进行初始化工作，最常见的就是对成员变量赋值。
 * 不管是声明还是定义，函数名前面都不能出现返回值类型，即使是 void 也不允许；函数体中不能有 return 语句。
 * 一个类必须有构造函数
 */
FusionEKF::FusionEKF() {
  is_initialized_ = false;

  previous_timestamp_ = 0;

  // initializing matrices
  R_laser_ = MatrixXd(2, 2);
  R_radar_ = MatrixXd(3, 3);
  H_laser_ = MatrixXd(2, 4);
  Hj_ = MatrixXd(3, 4);

  // measurement covariance matrix - laser
  R_laser_ << 0.0225, 0,
              0, 0.0225;

  // measurement covariance matrix - radar
  R_radar_ << 0.09, 0, 0,
              0, 0.0009, 0,
              0, 0, 0.09;

  // measurement matrix - laser
  H_laser_ << 1, 0, 0, 0,
              0, 1, 0, 0;
  
  // measurement matrix(Jacobian) - radar
  Hj_ << 1, 1, 0, 0,
         1, 1, 0, 0,
         1, 1, 1, 1;
  
  // initialize translation matrix
  ekf_.F_ = MatrixXd(4,4);
  ekf_.F_ << 1, 0, 1, 0,
             0, 1, 0, 1,
             0, 0, 1, 0,
             0, 0, 0, 1;
  
  // initialize process noise covariance matrix
  ekf_.Q_ = MatrixXd(4,4);
  ekf_.Q_ << 0, 0, 0, 0,
             0, 0, 0, 0,
             0, 0, 0, 0,
             0, 0, 0, 0;
  
  // measurement noises
  noise_ax = 9;
  noise_ay = 9;
}

/**
 * Destructor.
 * 析构函数也是一种特殊的成员函数，没有返回值，不需要程序员显式调用（程序员也没法显式调用），而是在销毁对象时自动执行。
 * 构造函数的名字和类名相同，而析构函数的名字是在类名前面加一个~符号。
 * 注意：析构函数没有参数，不能被重载，因此一个类只能有一个析构函数。如果用户没有定义，编译器会自动生成一个默认的析构函数。
 */
FusionEKF::~FusionEKF() {}

void FusionEKF::ProcessMeasurement(const MeasurementPackage &measurement_pack) {
  /**
   * Initialization
   */
  if (!is_initialized_) {

    // Initialize the state ekf_.x_ with the first measurement
    // first measurement
    cout << "EKF: " << endl;
    ekf_.x_ = VectorXd(4);
    ekf_.x_ << 1, 1, 1, 1;

    // state covariance matrix (about the Gaussian distribution)
    // it's used to describe how certain the state variables (mean) are
    // normally, the x, y values (the first two elements) are relatively accurate, so their uncertainty is lower
    // but velocity vectors are not exact, so they have higer covariance value
    ekf_.P_ = MatrixXd(4,4);
    ekf_.P_ << 1, 0, 0, 0,
               0, 1, 0, 0,
               0, 0, 1000, 0,
               0, 0, 0, 1000;
    
    if (measurement_pack.sensor_type_ == MeasurementPackage::RADAR) {
      // Convert radar from polar to cartesian coordinates and initialize state.
        float rho = measurement_pack.raw_measurements_(0);
        float phi = measurement_pack.raw_measurements_(1);
        float rhodot = measurement_pack.raw_measurements_(2);
      

        float px = rho * cos(phi);
        float py = rho * sin(phi);
        float vx = rhodot * cos(phi);
        float vy = rhodot * sin(phi);
        ekf_.x_ << px, py, vx, vy;
      
    }
    else if (measurement_pack.sensor_type_ == MeasurementPackage::LASER) {
      // Initialize state.
        float px = measurement_pack.raw_measurements_(0);
        float py = measurement_pack.raw_measurements_(1);
        ekf_.x_ << px, py, 0.0, 0.0;
    }
    
    
    // initial timestamp
    previous_timestamp_ = measurement_pack.timestamp_;
    // done initializing, no need to predict or update
    is_initialized_ = true;
    return;
  }

  /**
   * Prediction
   */

  // compute the time elapsed between the current and previous measurements
  // time is measured in seconds
  float dt = (measurement_pack.timestamp_ - previous_timestamp_)/1000000.0;
  previous_timestamp_ = measurement_pack.timestamp_ ;
  float dt_2 = dt * dt;
  float dt_3 = dt_2 * dt;
  float dt_4 = dt_3 * dt; 
  
  // update the state transition matrix F according to the new elapsed time
  ekf_.F_(0, 2) = dt;
  ekf_.F_(1, 3) = dt;
  
  // update the process noise covariance matrix
  ekf_.Q_ = MatrixXd(4,4);
  ekf_.Q_<< dt_4/4*noise_ax, 0, dt_3/2*noise_ax, 0,
            0, dt_4/4*noise_ay, 0, dt_3/2*noise_ay,
            dt_3/2*noise_ax, 0, dt_2*noise_ax, 0,
            0, dt_3/2*noise_ay, 0, dt_2*noise_ay;
  
  ekf_.Predict();

  /**
   * Update
   */

  if (measurement_pack.sensor_type_ == MeasurementPackage::RADAR) {
    // Radar updates
    // Update Kalman Filter to use radar covariance matrix
    ekf_.R_ = R_radar_;
    // Calculate the Jacobian to linearise the measurement function
    Hj_ = tools.CalculateJacobian(ekf_.x_);
    ekf_.H_ = Hj_;
    // Update state using extended Kalman Filter
    ekf_.UpdateEKF(measurement_pack.raw_measurements_);
  } else {
    // Laser updates
    ekf_.R_ = R_laser_;
    ekf_.H_ = H_laser_;
    // Update state using Kalman Filter
    ekf_.Update(measurement_pack.raw_measurements_);

  }

  // print the output
  cout << "x_ = " << ekf_.x_ << endl;
  cout << "P_ = " << ekf_.P_ << endl;
}
