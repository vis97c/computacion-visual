import { useEffect, useRef, useMemo } from "react";
import { useGLTF, useAnimations } from "@react-three/drei";
import * as THREE from "three";

interface GirlProps {
	animation: string;
	onAnimationEnd?: (name: string) => void;
	onClick?: () => void;
	onPointerOver?: () => void;
}

export function Girl({ animation, onAnimationEnd, ...props }: GirlProps) {
	const group = useRef<THREE.Group>(null);
	const { scene } = useGLTF("/Girlscout T Masuyama/Girlscout T Masuyama.gltf");

	// Load all animation files
	const { animations: idleAnims } = useGLTF("/Idle/Idle.gltf");
	const { animations: waveAnims } = useGLTF("/Waving/Waving.gltf");
	const { animations: walkAnims } = useGLTF("/Walking/Walking.gltf");
	const { animations: jumpAnims } = useGLTF("/Jump/Jump.gltf");
	const { animations: t1Anims } = useGLTF("/Thriller Part 1/Thriller Part 1.gltf");
	const { animations: t2Anims } = useGLTF("/Thriller Part 2/Thriller Part 2.gltf");
	const { animations: t3Anims } = useGLTF("/Thriller Part 3/Thriller Part 3.gltf");
	const { animations: t4Anims } = useGLTF("/Thriller Part 4/Thriller Part 4.gltf");

	// Combine and rename animations
	const allAnimations = useMemo(() => {
		const anims: THREE.AnimationClip[] = [];
		const process = (clip: THREE.AnimationClip, name: string) => {
			if (clip) {
				const newClip = clip.clone();
				newClip.name = name;
				anims.push(newClip);
			}
		};

		if (idleAnims?.[0]) process(idleAnims[0], "idle");
		if (waveAnims?.[0]) process(waveAnims[0], "wave");
		if (walkAnims?.[0]) process(walkAnims[0], "run");
		if (jumpAnims?.[0]) process(jumpAnims[0], "jump");
		if (t1Anims?.[0]) process(t1Anims[0], "thriller1");
		if (t2Anims?.[0]) process(t2Anims[0], "thriller2");
		if (t3Anims?.[0]) process(t3Anims[0], "thriller3");
		if (t4Anims?.[0]) process(t4Anims[0], "thriller4");

		return anims;
	}, [idleAnims, waveAnims, walkAnims, jumpAnims, t1Anims, t2Anims, t3Anims, t4Anims]);

	const { actions, mixer } = useAnimations(allAnimations, group);

	// Handle animation transitions
	useEffect(() => {
		const currentAction = actions[animation];
		if (!currentAction) return;

		// Play the requested animation
		currentAction.reset().fadeIn(0.5).play();

		return () => {
			currentAction.fadeOut(0.5);
		};
	}, [animation, actions]);

	// Listen for animation finished event (useful for sequences)
	useEffect(() => {
		const handleFinished = (e: any) => {
			if (onAnimationEnd) {
				onAnimationEnd(e.action.getClip().name);
			}
		};

		mixer.addEventListener("finished", handleFinished);
		return () => mixer.removeEventListener("finished", handleFinished);
	}, [mixer, onAnimationEnd]);

	// Set loop mode for non-looping animations
	useEffect(() => {
		if (actions.wave) {
			actions.wave.setLoop(THREE.LoopRepeat, 3);
			actions.wave.timeScale = 0.8; // Slightly slower to make it more visible
		}
		if (actions.jump) actions.jump.setLoop(THREE.LoopOnce, 1);
		if (actions.thriller1) actions.thriller1.setLoop(THREE.LoopOnce, 1);
		if (actions.thriller2) actions.thriller2.setLoop(THREE.LoopOnce, 1);
		if (actions.thriller3) actions.thriller3.setLoop(THREE.LoopOnce, 1);
		if (actions.thriller4) actions.thriller4.setLoop(THREE.LoopOnce, 1);

		// Ensure they stop at the end so 'finished' event fires
		if (actions.wave) actions.wave.clampWhenFinished = true;
		if (actions.jump) actions.jump.clampWhenFinished = true;
		if (actions.thriller1) actions.thriller1.clampWhenFinished = true;
		if (actions.thriller2) actions.thriller2.clampWhenFinished = true;
		if (actions.thriller3) actions.thriller3.clampWhenFinished = true;
		if (actions.thriller4) actions.thriller4.clampWhenFinished = true;
	}, [actions]);

	return (
		<group
			ref={group}
			{...props}
			dispose={null}
			onClick={(e) => {
				e.stopPropagation();
				if (props.onClick) props.onClick();
			}}
			onPointerOver={(e) => {
				e.stopPropagation();
				if (props.onPointerOver) props.onPointerOver();
			}}
		>
			<primitive object={scene} />
		</group>
	);
}

// Preload models
useGLTF.preload("/Girlscout T Masuyama/Girlscout T Masuyama.gltf");
useGLTF.preload("/Idle/Idle.gltf");
useGLTF.preload("/Waving/Waving.gltf");
useGLTF.preload("/Walking/Walking.gltf");
useGLTF.preload("/Jump/Jump.gltf");
useGLTF.preload("/Thriller Part 1/Thriller Part 1.gltf");
useGLTF.preload("/Thriller Part 2/Thriller Part 2.gltf");
useGLTF.preload("/Thriller Part 3/Thriller Part 3.gltf");
useGLTF.preload("/Thriller Part 4/Thriller Part 4.gltf");
