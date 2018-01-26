import React from 'react';

class GraderManager extends React.Component {
    constructor(props) {
      super(props);
      this.state = {graders: [
                              {id: '1', first_name: 'John', last_name: 'Doe'},
                              {id: '2', first_name: 'Jan', last_name: 'Janssen'}
                            ],
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
  
    fetchData() {
      fetch('/api/graders', {credentials: 'same-origin'})
      .then((response) => response.json())
      .then((graders) =>{
        this.setState({graders: graders})
      })
    }

    clearNames() {
        this.setState({
            first_name: '',
            last_name: '',
        })
    }
  
    handleSubmit(event) {
      var data = {first_name: this.state.first_name,
                  last_name: this.state.last_name};
  
      fetch('/api/graders', {
        method: 'POST', // or 'PUT'
        body: JSON.stringify(data), 
        headers: new Headers({
          'Content-Type': 'application/json'
        })
      })
      .then(res => res.json())
      .catch(error => console.error('Error:', error))
      .then(response => {
          this.clearNames()
          this.fetchData()
      })
  
      event.preventDefault();
    }
  
    componentDidMount() {
      this.fetchData();
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
                {this.state.graders.map((grader) => {
                    return <li key={grader.id.toString()}>{grader.first_name + ' ' + grader.last_name}</li>
                })}
              </ul>
            </aside>
          </div>
      );
    }
  }
  
  export default GraderManager;
