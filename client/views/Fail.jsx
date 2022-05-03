import React from 'react'

const Home = (props) => {
  return (
    <div className='notification is-danger has-text-centered content'>

      <h1>Oops!</h1>

      <h5>{props.message ? props.message : "Something went wrong :'("}</h5>

    </div>
  )
}

export default Home
