#include "kalman_filter.h"

using Eigen::MatrixXd;
using Eigen::VectorXd;

/* 
 * Please note that the Eigen library does not initialize 
 *   VectorXd or MatrixXd objects with zeros upon creation.
 */

KalmanFilter::KalmanFilter() {}

KalmanFilter::~KalmanFilter() {}

void KalmanFilter::Init(VectorXd &x_in, MatrixXd &P_in, MatrixXd &F_in,
                        MatrixXd &H_in, MatrixXd &R_in, MatrixXd &Q_in) {
  x_ = x_in;
  P_ = P_in;
  F_ = F_in;
  H_ = H_in;
  R_ = R_in;
  Q_ = Q_in;
  
}

void KalmanFilter::Predict() {
  // State transition
  x_ = F_ * x_;
  // State covariance
  P_ = F_ * P_ * F_.transpose() + Q_;
}

void KalmanFilter::Update(const VectorXd &z) {
  // update the state by using Kalman Filter equations
  VectorXd y = z - H_ * x_;
  UpdateMeasurements(y);
}

void KalmanFilter::UpdateEKF(const VectorXd &z) {
  float px = x_[0];
  float py = x_[1];
  float vx = x_[2];
  float vy = x_[3];
  
  // check the value is not zero
  if (px == 0. && py == 0.)
     return;
  
  // calculate
  float rho = sqrt(px*px + py*py);
  float theta = atan2(py, px);
  
  // check division by zero
  if (rho < 0.0001) {
    rho = 0.0001;
  } 
  float rhodot = (px*vx + py*vy)/rho;
  
  // find hx
  VectorXd h(3);
  h << rho, theta, rhodot;
  VectorXd y = z - h;
  
  // normalise the angle
  while(y[1] > M_PI) y[1] -= 2. * M_PI;
  while(y[1] < -M_PI) y[1] += 2. * M_PI;
  
  UpdateMeasurements(y);
}

void KalmanFilter::UpdateMeasurements(const VectorXd &y){
  // measurement uncertainty
  MatrixXd S = H_ * P_ * H_.transpose() + R_;
  // Kalman gain (weighted combination of prediction and measurement uncertainty)
  MatrixXd K = P_ * H_.transpose() * S.inverse();
  // Updated state and covariance
  x_ = x_ + K * y;
  long x_size = x_.size();
  MatrixXd I = MatrixXd::Identity(x_size, x_size);
  P_ = (I - K * H_) * P_;

}