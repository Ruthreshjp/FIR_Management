import { createContext, useContext, useState, useEffect } from 'react'

const ProfileContext = createContext(null)

export function ProfileProvider({ children }) {
  const [profile, setProfile] = useState({
    officerName: 'Inspector Raj',
    rank: 'Sub-Inspector',
    badgeNumber: 'ID-10492',
    stationName: 'Central Police Station',
    district: 'Chennai City'
  })

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('autofir_profile')
    if (saved) {
      try {
        setProfile(JSON.parse(saved))
      } catch (e) {
        console.error(e)
      }
    }
  }, [])

  const saveProfile = (newProfile) => {
    setProfile(newProfile)
    localStorage.setItem('autofir_profile', JSON.stringify(newProfile))
  }

  return (
    <ProfileContext.Provider value={{ profile, saveProfile }}>
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  return useContext(ProfileContext)
}
