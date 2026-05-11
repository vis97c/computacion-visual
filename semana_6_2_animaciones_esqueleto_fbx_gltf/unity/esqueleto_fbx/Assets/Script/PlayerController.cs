using UnityEngine;

public sealed class PlayerController : MonoBehaviour
{
    private Animator _animator;
    private bool _isPaused = false;

    void Start() => _animator = GetComponent<Animator>();

    // Funciones para la UI 
    public void TogglePause()
    {
        _isPaused = !_isPaused;
        if (_isPaused)
        {
            _animator.speed = 0f;
        }
        else
        {
            _animator.speed = 1f;
        }
    }

    //Reiniciar la animación actual
    public void RestartAnimation()
    {
        _animator.Play(_animator.GetCurrentAnimatorStateInfo(0).fullPathHash, -1, 0f);
    }

    public void ChangeAnimation(int index)
    {
        // Ejemplo para un Dropdown
        if (index == 0) _animator.Play("Idle");
        if (index == 1) _animator.Play("Run");
        if (index == 2) _animator.Play("Walk");
        if (index == 3) _animator.Play("Jump");
    }

    // Asegúrate de que el script esté en el mismo objeto que el AudioSource
    private AudioSource _audioSource;

    void Awake()
    {
        _audioSource = GetComponent<AudioSource>();
    }

    // Esta es la función que llamaremos desde la animación
    public void PlayJumpSound()
    {
        if (_audioSource != null)
        {
            _audioSource.Play();
        }
    }
}