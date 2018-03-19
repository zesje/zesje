import React from 'react';
import * as api from "../api.jsx";

class GraderManager extends React.Component {
    constructor(props) {
      super(props);
      this.state = {graders: [],
                    first_name: '',
                    last_name: '' };
      
      this.handleInputChange = this.handleInputChange.bind(this);
      this.handleSubmit = this.handleSubmit.bind(this);
    }
  
    handleInputChange(event) {
      const target = event.target;
      const name = target.name;
  
      this.setState({[name]: target.value});
    }

    handleSubmit(event) {
      var data = {first_name: this.state.first_name,
                  last_name: this.state.last_name};

      api.post('graders', data)
      .then(graders => {
        this.setState({
            first_name: '',
            last_name: '',
            graders: graders,
        })
      })
      .catch(resp => {
          alert('could not save grader (see Javascript console for details)')
          console.error('Error saving grader:', resp)
      })
  
      event.preventDefault();
    }
  
    componentDidMount() {
      api.get('graders')
      .then(graders => {
        this.setState({graders: graders})
      })
      .catch(resp => {
          alert('could not fetch graders (see Javascript console for details)')
          console.error('Error fetching graders:', resp)
      })
    }
  
    render() {
      return (
            <div>
              <form onSubmit={this.handleSubmit}>
                <div className="field has-addons">
                <div className="control">
                  <input name="first_name" value={this.state.first_name} 
                    onChange={this.handleInputChange} className="input" type="text" 
                    placeholder="First name" />
                </div>
                <div className="control">
                  <input name="last_name" value={this.state.last_name}
                    onChange={this.handleInputChange} className="input" type="text"
                    placeholder="Surname" />
                </div>
                <div className="control">
                  <button type="submit" className="button is-info">
                    Add
                  </button>
                </div>
              </div>
            </form>
  
            <br />

            <aside className="menu">
              <p className="menu-label">
                Added graders
              </p>
              <ul className="menu-list">
                {this.state.graders.map((grader) =>
                    <li key={grader.id.toString()}>{grader.first_name + ' ' + grader.last_name}</li>
                )}
              </ul>
            </aside>
          </div>
      );
    }
  }
  
  export default GraderManager;
