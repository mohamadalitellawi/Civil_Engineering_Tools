from dataclasses import dataclass

@dataclass
class Material:
    fc: float # specified compressive strength of concrete, MPa
    fy: float # specified yield strength for nonprestressed rein-forcement,MPa

@dataclass
class Section_Dimensions:
    # Note that the dimension c33 is the depth of the Section in the 2-2 direction and contributes primarily to I33.
    section_c22:float # cross section width, mm
    section_c33 :float # cross section length, mm
    section_cc :float # 20.5.1.3 clear cover of reinforcement, mm
    rft_ratio :float # reinforcements ratio of longitudinal bars

@dataclass
class Load_Case:
    # factored axial force; to be taken as positive for compression and negative for tension, N
    Pu :float # ultimate design axial force, N
    Pu_sustained:float # ultimate sustained axial force, N
    Mu_22 :float # ultimate desigm moment about local axis 2-2 as per ETABS, N*mm
    Mu_33 :float  # ultimate desigm moment about local axis 3-3 as per ETABS, N*mm

    def import_from_etabs(self, 
                          force_unit_scale:float = 1e3, 
                          moment_unit_scale:float = 1e6, 
                          flip_axial_sign:bool = True,
                          moment_absolute:bool = True) :
        self.Pu *= force_unit_scale
        self.Pu_sustained *= force_unit_scale
        self.Mu_22 *= moment_unit_scale
        self.Mu_33 *= moment_unit_scale
        if flip_axial_sign:
            self.Pu *= -1
            self.Pu_sustained *= -1
        if moment_absolute:
            self.Mu_22 = abs(self.Mu_22)
            self.Mu_33 = abs(self.Mu_33)
        return self



def calculate_column_actual_moment_of_inertia(material:Material, dimensions:Section_Dimensions, loads:Load_Case,rounding_digits:int = 3) -> float:
    '''
    calculate moments of inertia for elastic analysis at factored load
    as per ACI318-19 Table 6.6.3.1.1(b)
    '''
    Ag = dimensions.section_c22 * dimensions.section_c33 # gross area of concrete section, mm²
    Ast = Ag * dimensions.rft_ratio # total area of longitudinal reinforcement bars, mm²
    Po = 0.85 * material.fc * (Ag - Ast) + material.fy * Ast # 22.4.2.2 nominal axial strength at zero eccentricity, N

    Ig_22 = dimensions.section_c33 * dimensions.section_c22**3 / 12 # moment of inertia of gross concrete section about centroidal axis, neglecting reinforcement, mm⁴
    Ig_33 = dimensions.section_c22 * dimensions.section_c33**3 / 12 # moment of inertia of gross concrete section about centroidal axis, neglecting reinforcement, mm⁴

    I22_calculated = (0.8 + 25 * Ast / Ag)*(1 - (loads.Mu_22/(loads.Pu*dimensions.section_c22)) - 0.5 * (loads.Pu/Po)) * Ig_22 # Table 6.6.3.1.1(b)
    I33_calculated = (0.8 + 25 * Ast / Ag)*(1 - (loads.Mu_33/(loads.Pu*dimensions.section_c33)) - 0.5 * (loads.Pu/Po)) * Ig_33 # Table 6.6.3.1.1(b)

    I22 = max(min(I22_calculated,0.875 * Ig_22),0.35 * Ig_22)
    I33 = max(min(I33_calculated,0.875 * Ig_33),0.35 * Ig_33)

    return {'moment_of_inertia':(round(I22,rounding_digits),round(I33,rounding_digits)), 
            'ratio':(round(I22/Ig_22,rounding_digits),round(I33/Ig_33,rounding_digits))}

