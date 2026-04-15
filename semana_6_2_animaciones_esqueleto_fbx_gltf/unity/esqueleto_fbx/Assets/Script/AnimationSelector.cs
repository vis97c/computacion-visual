using UnityEngine;
using UnityEngine.UI; // Importante para trabajar con UI

public sealed class AnimationSelector : MonoBehaviour
{
    private Animator _animator;

    void Start()
    {
        _animator = GetComponent<Animator>();
    }

    // Esta función será llamada por el Dropdown
    public void SelectAnimationFromDropdown(int index)
    {
        switch (index)
        {
            case 0:
                _animator.Play("Idle"); // Nombre exacto del estado en el Animator
                break;
            case 1:
                _animator.Play("Run");
                break;
            case 2:
                _animator.Play("Walk");
                break;
            case 3:
                _animator.Play("Jump");
            break;
        }
    }
}