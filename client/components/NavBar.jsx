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

            <button className="button navbar-burger" onClick={() => { 
                let menu = document.querySelector(".navbar-menu");
                menu.classList.toggle("is-active"); 
              }}>
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>

          <div className="navbar-menu">
            <div className="navbar-start">
              <Link className="navbar-item" to='/'>Home</Link>
              <Link className="navbar-item" to='/exams'>Exams</Link>
              <Link className="navbar-item" to='/students'>Match Submissions</Link>
              <a class="navbar-item" href="/dashboards/grade">Grade</a>
            </div>

            <div className="navbar-end">
              <Link className="navbar-item" to='/graders'>Manage graders</Link>
              <a class="navbar-item" href="/dashboards/add-graders-and-students">Manage Students</a>
              <div className="navbar-item">
                <i>Version 0.6.4</i>
              </div>
            </div>
          </div>
        </nav>
  )
}

export default NavBar;
