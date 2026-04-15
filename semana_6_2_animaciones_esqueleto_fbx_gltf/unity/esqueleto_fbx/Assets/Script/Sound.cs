using UnityEngine;

public class Sound : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        AudioSource audioSource = GetComponent<AudioSource>();
    }

    public void PlaySound()
    {
        AudioSource audioSource = GetComponent<AudioSource>();
        audioSource.Play();
    }
}
