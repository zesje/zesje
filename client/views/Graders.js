import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';


class GraderList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {graders: [
      {id: '1', name: 'John Doe'},
      {id: '2', name: 'Jan Janssen'}
    ]};
  }

  componentDidMount() {
   
  }

  componentWillUnmount() {
    
  }


  render() {
    return (
      <div className="select">
        <aside className="menu">
          <p className="menu-label">
            Added graders
          </p>
          <ul className="menu-list">
            {this.state.graders.map(function(grader) {
              <li>{grader.name}</li>
            })}
          </ul>
        </aside>
      </div>
    );
  }
}

const Graders = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Manage Graders' subtitle='Many hands make light work' />
        
        <section className="section">


          <div className="container">
            <h1 className='title'>Enter the names</h1>
            <h5 className='subtitle'>to add them to the system</h5>
            
            <hr />

            <div className="field has-addons">
              <div className="control">
                <input className="input" type="text" placeholder="Add someone" />
              </div>
              <div className="control">
                <a className="button is-info">
                  Add
                </a>
              </div>
            </div>
            
            <GraderList />


          </div>
        </section>

        <Footer />

      </div>
  )
}

export default Graders;
