import React from 'react';
import { Link } from 'react-router-dom';

const NavBar = () => {
  return (
        <nav className="navbar" role="navigation" aria-label="dropdown navigation">
          
          <div className="navbar-brand">
            <div className="navbar-item has-text-info">
              <span className="icon">
                <i className="fa fa-edit fa-3x"></i>
              </span>
            </div>
            <div className="navbar-item has-text-info">
              <b>Zesje</b>
            </div>
          </div>

          <div className="navbar-menu">
            <div className="navbar-start">
              <Link className="navbar-item" to='/'>Home</Link>
              <Link className="navbar-item" to='/grade'>grade</Link>
              <Link className="navbar-item" to='/upload'>upload</Link>

              <div className="navbar-item has-dropdown is-hoverable">
                <a className="navbar-link">
                  People
                </a>
                <div className="navbar-dropdown">
                  <Link className="navbar-item" to='/addstudents'>Add students</Link>
                  <Link className="navbar-item" to='/checkstudents'>Check students</Link>
                  <hr className="navbar-divider" />
                  <Link className="navbar-item" to='/addgraders'>Add graders</Link>
                </div>
              </div>
              
            </div>

            <div className="navbar-end">
              <Link className="navbar-item has-text-info" to='/reset'>reset</Link>
              <div className="navbar-item">
                <i>Version 0.6.4</i>
              </div>
            </div>
          </div>
        </nav>
  )
}

export default NavBar;
