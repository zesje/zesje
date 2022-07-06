import React from 'react'

const Home = (props) => {
  return (
    <div className='notification is-danger has-text-centered content'>

      <h1 className='has-text-white'>Oops!</h1>

      <h4 className='has-text-white'>{props.message ? props.message : "Something went wrong :'("}</h4>

    </div>
  )
}

export default Home
